"""Flask API routes"""
from flask import Blueprint, request, jsonify, send_file
import logging
import os
import json
from typing import Dict, Any, List

from models.database import db, Brand, IntelligenceReport
from services.intelligence_engine import IntelligenceEngine
from utils.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__, url_prefix='/api')  

# Initialize services
intelligence_engine = IntelligenceEngine()
report_generator = ReportGenerator()


def _brand_slug(brand_name: str) -> str:
    return str(brand_name or '').strip().lower().replace(' ', '_')


def _build_ask_response(brand_name: str, question: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Create a richer text response with brand-specific follow-up questions."""
    competitor_data = analysis.get('competitor_data', []) or []
    market = analysis.get('market_analysis', {}) or {}
    campaign = analysis.get('campaign_recommendations', {}) or {}

    competitor_names = [c.get('competitor_name', 'Unknown') for c in competitor_data[:8]]
    top_competitor = competitor_names[0] if competitor_names else 'Unknown'
    top_threats = market.get('key_threats', [])[:3]
    top_opportunities = market.get('opportunities', [])[:3]
    gtm_items = campaign.get('gtm_recommendations', [])[:3]
    question_lc = question.strip().lower()

    weakness_lines: List[str] = []
    for comp in competitor_data[:3]:
        name = comp.get('competitor_name', 'Competitor')
        gaps = (comp.get('insights', {}) or {}).get('market_gaps', [])
        if gaps:
            weakness_lines.append(f"{name}: {gaps[0]}")
    if not weakness_lines:
        weakness_lines.append('No explicit weakness signal was captured in this run; use G2/review scraping refresh.')

    section_lines: List[str] = []
    section_lines.append(f"Brand: {brand_name}")
    section_lines.append(f"Question: {question.strip()}")
    section_lines.append("")
    section_lines.append("Competitive Snapshot")
    section_lines.append(f"- Top competitor pressure: {top_competitor}")
    section_lines.append(f"- Active competitors tracked: {', '.join(competitor_names) if competitor_names else 'N/A'}")
    section_lines.append(f"- Threat level: {market.get('threat_level', 'N/A')}")
    section_lines.append("")
    section_lines.append("Top Threats")
    for item in (top_threats or ['No threat signal captured in this run.']):
        section_lines.append(f"- {item}")
    section_lines.append("")
    section_lines.append("Top Opportunities")
    for item in (top_opportunities or ['No opportunity signal captured in this run.']):
        section_lines.append(f"- {item}")
    section_lines.append("")
    section_lines.append("Competitor Weaknesses You Can Exploit")
    for item in weakness_lines:
        section_lines.append(f"- {item}")

    if 'price' in question_lc or 'pricing' in question_lc:
        section_lines.append("")
        section_lines.append("Pricing Angle")
        section_lines.append("- Position value as faster time-to-value with lower operational friction.")
        section_lines.append("- Counter enterprise complexity with simple, predictable packaging.")
    if 'campaign' in question_lc or 'go to market' in question_lc or 'gtm' in question_lc:
        section_lines.append("")
        section_lines.append("Campaign Priorities")
        for rec in gtm_items:
            section_lines.append(f"- {rec.get('title', 'N/A')}: {rec.get('description', 'N/A')}")

    follow_up_questions = [
        f"Which competitor is easiest for {brand_name} to displace in the next 90 days and why?",
        f"What messaging should {brand_name} use against {top_competitor} for enterprise buyers?",
        f"What are the top 3 campaign experiments for {brand_name} this month?",
        f"Which channels should {brand_name} prioritize for fastest pipeline impact?"
    ]

    return {
        'answer': '\n'.join(section_lines),
        'follow_up_questions': follow_up_questions
    }


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'KeenFox Intelligence Engine'
    }), 200


@bp.route('/analyze', methods=['POST'])
def analyze_brand():
    """Analyze a brand and its competitors"""
    try:
        data = request.get_json() or {}
        brand_name = data.get('brand_name')
        competitor_count = data.get('competitor_count', 8)
        
        if not brand_name:
            return jsonify({'error': 'brand_name is required'}), 400
        
        logger.info(f"Starting analysis for brand: {brand_name} | requested competitors: {competitor_count}")

        existing_brand = Brand.query.filter_by(name=brand_name).first()
        previous_report = None
        previous_analysis = None
        if existing_brand:
            previous_report = (
                IntelligenceReport.query
                .filter_by(brand_id=existing_brand.id)
                .order_by(IntelligenceReport.created_at.desc())
                .first()
            )
            if previous_report and previous_report.report_data:
                try:
                    previous_analysis = json.loads(previous_report.report_data)
                except json.JSONDecodeError:
                    previous_analysis = None
        
        # Run analysis
        try:
            competitor_count = int(competitor_count)
        except (TypeError, ValueError):
            return jsonify({'error': 'competitor_count must be an integer', 'status': 'error'}), 400

        if competitor_count < 1 or competitor_count > 12:
            return jsonify({'error': 'competitor_count must be between 1 and 12', 'status': 'error'}), 400

        analysis_result = intelligence_engine.analyze_brand(brand_name, competitor_limit=competitor_count)
        
        # Save to database
        brand_id = intelligence_engine.save_analysis_to_db(brand_name, analysis_result)
        
        # Generate reports
        reports = report_generator.generate_all_formats(
            brand_name,
            analysis_result,
            previous_analysis=previous_analysis
        )

        # Persist one primary report entry for listing/history.
        summary = (
            analysis_result.get('campaign_recommendations', {}).get('overall_strategy')
            or f"Competitive intelligence summary for {brand_name}."
        )
        key_findings = analysis_result.get('market_analysis', {}).get('key_threats', [])[:5]

        primary_report_path = reports.get('json') or next(iter(reports.values()), None)
        report_record = IntelligenceReport(
            brand_id=brand_id,
            report_title=f"{brand_name} — Competitive Intelligence Report",
            report_data=json.dumps(analysis_result),
            summary=summary,
            key_findings=json.dumps(key_findings),
            competitors_analyzed=analysis_result.get('competitors_analyzed', 0),
            signals_extracted=analysis_result.get('signals_extracted', 0),
            file_path=primary_report_path,
            file_format='json'
        )
        db.session.add(report_record)
        db.session.commit()

        # Convert local file paths to API download URLs.
        report_links = {}
        for fmt, path in reports.items():
            if not path:
                continue
            filename = os.path.basename(path)
            report_links[fmt] = f"/api/reports/files/{filename}"
        
        report_payload = None
        report_json_path = reports.get('json')
        if report_json_path and os.path.exists(report_json_path):
            try:
                with open(report_json_path, 'r', encoding='utf-8') as report_file:
                    report_payload = json.load(report_file)
            except Exception as read_exc:
                logger.warning(f"Could not load generated JSON report payload: {read_exc}")

        # Always publish the latest generated report into a deterministic check file.
        if report_payload:
            backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            latest_check_path = os.path.join(backend_root, f"{_brand_slug(brand_name)}_latest_check.txt")
            try:
                with open(latest_check_path, 'w', encoding='utf-8') as latest_file:
                    latest_file.write(json.dumps(report_payload, indent=2))
            except Exception as write_exc:
                logger.warning(f"Could not write latest check file: {write_exc}")

        response = {
            'status': 'success',
            'brand_id': brand_id,
            'brand_name': brand_name,
            'competitor_count_requested': competitor_count,
            'analysis': analysis_result,
            'report': report_payload,
            'reports': report_links,
            'message': f'Analysis complete for {brand_name}'
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error analyzing brand: {e}", exc_info=True)
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.route('/brands', methods=['GET'])
def get_brands():
    """Get list of analyzed brands"""
    try:
        brands = Brand.query.all()
        return jsonify({
            'status': 'success',
            'count': len(brands),
            'brands': [b.to_dict() for b in brands]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching brands: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.route('/brand/<brand_id>', methods=['GET'])
def get_brand_details(brand_id):
    """Get details for a specific brand"""
    try:
        brand = Brand.query.get(brand_id)
        if not brand:
            return jsonify({'error': 'Brand not found'}), 404
        
        # Get comparative insights
        insights = intelligence_engine.get_comparative_insights(brand_id)
        
        return jsonify({
            'status': 'success',
            'brand': brand.to_dict(),
            'insights': insights
        }), 200
    except Exception as e:
        logger.error(f"Error fetching brand details: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.route('/reports', methods=['GET'])
def get_reports():
    """Get list of generated reports"""
    try:
        reports = IntelligenceReport.query.order_by(IntelligenceReport.created_at.desc()).all()
        return jsonify({
            'status': 'success',
            'count': len(reports),
            'reports': [r.to_dict() for r in reports]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching reports: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.route('/reports/<report_id>/download', methods=['GET'])
def download_report(report_id):
    """Download a report file"""
    try:
        report = IntelligenceReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        file_path = report.file_path
        if not os.path.exists(file_path):
            return jsonify({'error': 'Report file not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.route('/reports/files/<filename>', methods=['GET'])
def download_report_file(filename):
    """Download a report directly by generated filename."""
    try:
        safe_name = os.path.basename(filename)
        file_path = os.path.join(report_generator.output_dir, safe_name)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Report file not found'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=safe_name
        )
    except Exception as e:
        logger.error(f"Error downloading report file: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.route('/competitors/<brand_id>', methods=['GET'])
def get_competitors(brand_id):
    """Get detailed competitor analysis for a brand"""
    try:
        brand = Brand.query.get(brand_id)
        if not brand:
            return jsonify({'error': 'Brand not found'}), 404
        
        from models.database import CompetitorAnalysis
        competitors = CompetitorAnalysis.query.filter_by(brand_id=brand_id).all()
        
        return jsonify({
            'status': 'success',
            'brand_name': brand.name,
            'competitors_count': len(competitors),
            'competitors': [c.to_dict() for c in competitors]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching competitors: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.route('/search', methods=['GET'])
def search_brands():
    """Search brands by name"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        brands = Brand.query.filter(Brand.name.ilike(f'%{query}%')).limit(10).all()
        
        return jsonify({
            'status': 'success',
            'query': query,
            'count': len(brands),
            'results': [b.to_dict() for b in brands]
        }), 200
    except Exception as e:
        logger.error(f"Error searching brands: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        total_brands = Brand.query.count()
        from models.database import CompetitorAnalysis, IntelligenceReport
        total_competitors = CompetitorAnalysis.query.count()
        total_reports = IntelligenceReport.query.count()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_brands_analyzed': total_brands,
                'total_competitors_tracked': total_competitors,
                'total_reports_generated': total_reports,
                'average_competitors_per_brand': (
                    total_competitors // total_brands if total_brands > 0 else 0
                )
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.route('/ask', methods=['POST'])
def ask_intelligence():
    """Answer brand-specific questions using current analysis context."""
    try:
        data = request.get_json() or {}
        brand_name = (data.get('brand_name') or '').strip()
        question = (data.get('question') or '').strip()
        if not brand_name:
            return jsonify({'error': 'brand_name is required', 'status': 'error'}), 400
        if not question:
            return jsonify({'error': 'question is required', 'status': 'error'}), 400

        analysis = data.get('analysis')
        if not isinstance(analysis, dict):
            brand = Brand.query.filter_by(name=brand_name).first()
            if not brand:
                return jsonify({'error': 'No analysis found for brand. Run analysis first.', 'status': 'error'}), 404

            latest_report = (
                IntelligenceReport.query
                .filter_by(brand_id=brand.id)
                .order_by(IntelligenceReport.created_at.desc())
                .first()
            )
            if not latest_report or not latest_report.report_data:
                return jsonify({'error': 'No report data found for brand.', 'status': 'error'}), 404

            analysis = json.loads(latest_report.report_data)

        ask_payload = _build_ask_response(brand_name, question, analysis)
        return jsonify({
            'status': 'success',
            'brand_name': brand_name,
            'question': question,
            'answer': ask_payload['answer'],
            'follow_up_questions': ask_payload['follow_up_questions']
        }), 200
    except Exception as e:
        logger.error(f"Error in ask endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e), 'status': 'error'}), 500


@bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found', 'status': 'error'}), 404


@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error', 'status': 'error'}), 500
