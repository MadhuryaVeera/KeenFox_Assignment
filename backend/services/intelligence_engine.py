"""Core Intelligence Engine service"""
import logging
from typing import Dict, List, Any
from datetime import datetime
import json

from models.database import db, Brand, CompetitorAnalysis, WebSignal
from services.llm_service import LLMService
from services.web_scraper import WebScraperService
from services.guardrails_service import GuardrailsService

logger = logging.getLogger(__name__)


# Category-aware competitor catalogs so the same competitor list is not reused for every brand.
CATEGORY_COMPETITORS = {
    'productivity': {
        'Notion': {
            'website': 'https://www.notion.so',
            'features': ['Docs', 'Databases', 'Wikis', 'Templates', 'AI', 'Collaboration'],
            'messaging': ['The connected workspace', 'Build anything, together', 'Flexible by design'],
            'weaknesses': ['Can feel complex at scale', 'Performance with huge databases', 'Advanced governance setup']
        },
        'Coda': {
            'website': 'https://coda.io',
            'features': ['Docs', 'Tables', 'Automations', 'Packs', 'Buttons'],
            'messaging': ['All-in-one collaborative workspace', 'Docs that act like apps', 'AI-powered workflows'],
            'weaknesses': ['Steep learning curve', 'Can overwhelm new users', 'Performance with large docs']
        },
        'ClickUp': {
            'website': 'https://clickup.com',
            'features': ['Tasks', 'Docs', 'Dashboards', 'Goals', 'Automations'],
            'messaging': ['One app to replace them all', 'Business OS for teams', 'AI-powered productivity'],
            'weaknesses': ['Feature bloat', 'Complex onboarding', 'Support concerns']
        },
        'Airtable': {
            'website': 'https://airtable.com',
            'features': ['Base building', 'Automations', 'Interfaces', 'Views', 'AI'],
            'messaging': ['Low-code for work', 'Build apps on data', 'Enterprise ready'],
            'weaknesses': ['Pricing scales with usage', 'Advanced setup complexity', 'Requires tuning for specific workflows']
        },
        'Obsidian': {
            'website': 'https://obsidian.md',
            'features': ['Graph view', 'Markdown notes', 'Plugins', 'Local vaults', 'Bases'],
            'messaging': ['Sharpen your thinking', 'Private by default', 'Your notes, your control'],
            'weaknesses': ['Mobile limitations', 'Collaboration is add-on heavy', 'Less out-of-the-box team workflow']
        },
        'Confluence': {
            'website': 'https://www.atlassian.com/software/confluence',
            'features': ['Knowledge base', 'Page hierarchies', 'Jira integration', 'Templates', 'AI summaries'],
            'messaging': ['Team workspace for knowledge', 'Connected to Jira', 'Centralized collaboration'],
            'weaknesses': ['Approval flow complexity', 'Clutter at scale', 'Steep admin overhead']
        },
        'Google Workspace': {
            'website': 'https://workspace.google.com',
            'features': ['Docs', 'Sheets', 'Drive', 'Meet', 'Gemini AI'],
            'messaging': ['AI-powered collaboration', 'Cloud-native productivity', 'One suite for work'],
            'weaknesses': ['Admin complexity', 'Pricing opacity at scale', 'Workspace sprawl']
        },
        'Slack': {
            'website': 'https://slack.com',
            'features': ['Channels', 'Workflow automation', 'Search', 'Huddles', 'AI'],
            'messaging': ['Where work happens', 'Connected team communication', 'AI for productivity'],
            'weaknesses': ['Fragmentation into chat-only use cases', 'Pricing grows with teams', 'Knowledge base limitations']
        },
        'Asana': {
            'website': 'https://www.asana.com',
            'features': ['Project management', 'Task tracking', 'Timeline', 'Portfolio', 'Goals'],
            'messaging': ['Get your team aligned', 'Work management platform', 'Enterprise focus'],
            'weaknesses': ['Complex UI', 'Expensive pricing', 'Requires setup time']
        },
        'Monday.com': {
            'website': 'https://www.monday.com',
            'features': ['Work OS', 'Automation', 'Integration hub', 'Custom views', 'Templates'],
            'messaging': ['Manage any type of work', 'Work OS for organizations', 'Visual management'],
            'weaknesses': ['Pricing is high', 'Limited data analytics', 'Customization difficult']
        },
        'Microsoft 365 Copilot': {
            'website': 'https://www.microsoft.com/en-us/microsoft-365/copilot',
            'features': ['Copilot', 'Teams', 'Office apps', 'OneDrive', 'Outlook'],
            'messaging': ['AI inside Microsoft 365', 'Enterprise integration', 'Connected productivity'],
            'weaknesses': ['Complex suite pricing', 'Enterprise overhead', 'Learning curve']
        },
        'Trello': {
            'website': 'https://trello.com',
            'features': ['Kanban boards', 'Automation', 'Templates', 'Collaboration'],
            'messaging': ['Simple visual project management', 'Boards for everything'],
            'weaknesses': ['Limited advanced reporting', 'Can be too basic for enterprise']
        },
        'Wrike': {
            'website': 'https://www.wrike.com',
            'features': ['Work management', 'Resource planning', 'Dashboards', 'Automation'],
            'messaging': ['Work your way', 'Enterprise work management'],
            'weaknesses': ['Steep onboarding', 'Pricing complexity']
        },
        'Airtable': {
            'website': 'https://www.airtable.com',
            'features': ['Database platform', 'Views', 'Automations', 'Interfaces'],
            'messaging': ['Build apps on top of data', 'Flexible workflows'],
            'weaknesses': ['Cost scales quickly', 'Not ideal for heavy PM use cases']
        }
    },
    'ecommerce': {
        'Shopify': {
            'website': 'https://www.shopify.com',
            'features': ['Storefronts', 'Checkout', 'Payments', 'Apps', 'AI'],
            'messaging': ['Begin your entrepreneurial journey', 'Commerce without complexity', 'Built for scaling brands'],
            'weaknesses': ['App ecosystem dependence', 'Transaction fees', 'Scaling costs']
        },
        'BigCommerce': {
            'website': 'https://www.bigcommerce.com',
            'features': ['B2B ecommerce', 'Checkout customization', 'Catalog management', 'Headless commerce'],
            'messaging': ['Open SaaS for ambitious brands', 'Enterprise ecommerce'],
            'weaknesses': ['Complex implementation', 'Pricing at scale']
        },
        'Adobe Commerce': {
            'website': 'https://business.adobe.com/products/magento/magento-commerce.html',
            'features': ['Enterprise commerce', 'Customization', 'Scalability', 'B2B features'],
            'messaging': ['Powerful commerce platform', 'Built for complex businesses'],
            'weaknesses': ['High implementation cost', 'Technical complexity']
        },
        'WooCommerce': {
            'website': 'https://woocommerce.com',
            'features': ['WordPress integration', 'Plugins', 'Store control', 'Flexible checkout'],
            'messaging': ['Sell anything, beautifully', 'Open-source commerce'],
            'weaknesses': ['Performance tuning', 'Maintenance burden']
        },
        'Squarespace': {
            'website': 'https://www.squarespace.com',
            'features': ['Website builder', 'Ecommerce', 'Templates', 'Payments'],
            'messaging': ['Beautiful commerce made simple', 'All-in-one brand platform'],
            'weaknesses': ['Less enterprise depth', 'Customization ceiling']
        },
        'Wix': {
            'website': 'https://www.wix.com',
            'features': ['Website builder', 'Storefronts', 'Payments', 'AI tools'],
            'messaging': ['Create and scale online stores', 'Easy site building'],
            'weaknesses': ['Advanced commerce limitations', 'Scaling complexity']
        },
        'PrestaShop': {
            'website': 'https://www.prestashop.com',
            'features': ['Open-source commerce', 'Catalog management', 'Modules', 'International selling'],
            'messaging': ['Build your ecommerce freedom', 'Flexible open-source commerce'],
            'weaknesses': ['Technical setup burden', 'Plugin maintenance']
        }
    },
    'sportswear': {
        'Nike': {
            'website': 'https://www.nike.com',
            'features': ['Footwear', 'Apparel', 'Training', 'Membership', 'Digital ecosystem'],
            'messaging': ['Just do it', 'Athlete-first innovation', 'Performance and culture'],
            'weaknesses': ['Premium pricing', 'Demand sensitivity', 'Inventory swings']
        },
        'Adidas': {
            'website': 'https://www.adidas.com',
            'features': ['Footwear', 'Apparel', 'Performance gear', 'Brand collaborations'],
            'messaging': ['Impossible is nothing', 'Performance and style'],
            'weaknesses': ['Premium pricing', 'Inventory challenges']
        },
        'Puma': {
            'website': 'https://us.puma.com',
            'features': ['Athletic footwear', 'Apparel', 'Lifestyle products'],
            'messaging': ['Forever faster', 'Sport meets style'],
            'weaknesses': ['Lower premium perception', 'Narrower market share']
        },
        'Under Armour': {
            'website': 'https://www.underarmour.com',
            'features': ['Training gear', 'Running shoes', 'Performance apparel'],
            'messaging': ['Protect this house', 'Performance focus'],
            'weaknesses': ['Lifestyle appeal', 'Global brand breadth']
        },
        'New Balance': {
            'website': 'https://www.newbalance.com',
            'features': ['Running shoes', 'Athleisure', 'Comfort-focused footwear'],
            'messaging': ['Fearlessly independent', 'Comfort and performance'],
            'weaknesses': ['Less hype-driven positioning', 'Fashion collaboration dependence']
        },
        'Reebok': {
            'website': 'https://www.reebok.com',
            'features': ['Training shoes', 'Fitness apparel', 'Retro collaborations'],
            'messaging': ['Be more human', 'Fitness-first heritage'],
            'weaknesses': ['Smaller market share', 'Weaker premium position']
        },
        'ASICS': {
            'website': 'https://www.asics.com',
            'features': ['Running shoes', 'Performance apparel', 'Sport science'],
            'messaging': ['Sound mind, sound body', 'Performance running'],
            'weaknesses': ['Narrower lifestyle appeal', 'Lower mainstream visibility']
        }
    },
    'electronics': {
        'LG': {
            'website': 'https://www.lg.com',
            'features': ['Smart TVs', 'Home appliances', 'Displays', 'AI-powered devices'],
            'messaging': ["Life's Good", 'Innovation for everyday life', 'Connected home experiences'],
            'weaknesses': ['Price competition', 'Category spread', 'Brand differentiation in crowded segments']
        },
        'Samsung': {
            'website': 'https://www.samsung.com',
            'features': ['TVs', 'Home appliances', 'Smart devices', 'Displays'],
            'messaging': ['Do what you cannot', 'Connected living'],
            'weaknesses': ['Premium pricing', 'Complex product lines']
        },
        'Sony': {
            'website': 'https://www.sony.com',
            'features': ['TVs', 'Audio', 'Cameras', 'Entertainment devices'],
            'messaging': ['Like no other', 'Premium entertainment'],
            'weaknesses': ['High price points', 'Narrower appliance depth']
        },
        'Panasonic': {
            'website': 'https://www.panasonic.com',
            'features': ['Home appliances', 'TVs', 'Audio', 'Battery tech'],
            'messaging': ['A better life, a better world', 'Reliable electronics'],
            'weaknesses': ['Brand energy is softer', 'Less category buzz']
        },
        'Philips': {
            'website': 'https://www.philips.com',
            'features': ['Home appliances', 'Personal care', 'Lighting', 'Healthcare tech'],
            'messaging': ['Innovation and you', 'Everyday life improvement'],
            'weaknesses': ['Mixed category identity', 'Less display leadership']
        },
        'TCL': {
            'website': 'https://www.tcl.com',
            'features': ['TVs', 'Soundbars', 'Smart home', 'Mobile devices'],
            'messaging': ['Inspire greatness', 'Value-led innovation'],
            'weaknesses': ['Lower premium perception', 'Brand trust gap']
        },
        'Hisense': {
            'website': 'https://www.hisense.com',
            'features': ['TVs', 'Appliances', 'Smart home', 'Value pricing'],
            'messaging': ['Go big, go Hisense', 'Accessible innovation'],
            'weaknesses': ['Lower premium perception', 'Less category prestige']
        }
    },
    'beverages': {
        'Coca-Cola': {
            'website': 'https://www.coca-cola.com',
            'features': ['Soft drinks', 'Brand campaigns', 'Flavor portfolio'],
            'messaging': ['Real magic', 'Open happiness'],
            'weaknesses': ['Health concerns', 'Category parity']
        },
        'Pepsi': {
            'website': 'https://www.pepsi.com',
            'features': ['Carbonated soft drinks', 'Flavor variants', 'Brand campaigns'],
            'messaging': ['For the love of it', 'Refreshment and culture'],
            'weaknesses': ['Category parity', 'Health perception']
        },
        'Sprite': {
            'website': 'https://www.sprite.com',
            'features': ['Lemon-lime soda', 'Flavor positioning', 'Global distribution'],
            'messaging': ['Obey your thirst', 'Crisp refreshment'],
            'weaknesses': ['Narrower product line', 'Brand differentiation limits']
        },
        'Dr Pepper': {
            'website': 'https://www.drpepper.com',
            'features': ['Distinct flavor', 'Soda portfolio', 'Cultural branding'],
            'messaging': ['One of a kind', 'Unique taste'],
            'weaknesses': ['Smaller global footprint', 'Less health-forward']
        },
        'Fanta': {
            'website': 'https://www.fanta.com',
            'features': ['Fruit soda', 'Youthful branding', 'Global flavors'],
            'messaging': ['More fanta', 'Fun refreshment'],
            'weaknesses': ['Flavor-specific dependence', 'Lower adult appeal']
        },
        'Mountain Dew': {
            'website': 'https://www.mountaindew.com',
            'features': ['Citrus soda', 'Energy positioning', 'Youth branding'],
            'messaging': ['Do the dew', 'High-energy refreshment'],
            'weaknesses': ['Health concerns', 'Niche demographic concentration']
        },
        '7Up': {
            'website': 'https://www.7up.com',
            'features': ['Lemon-lime soda', 'Refreshment', 'Mixers'],
            'messaging': ['Make 7UP yours', 'Cool and crisp'],
            'weaknesses': ['Lower category differentiation', 'Smaller product portfolio']
        }
    },
    'electronics': {
        'Samsung': {
            'website': 'https://www.samsung.com',
            'features': ['Smart TVs', 'Appliances', 'Mobile devices', 'Home ecosystem'],
            'messaging': ['Bring home the future', 'Connected living', 'Premium innovation'],
            'weaknesses': ['Premium pricing', 'Complex product lines']
        },
        'Sony': {
            'website': 'https://www.sony.com',
            'features': ['Entertainment systems', 'TVs', 'Audio', 'Gaming ecosystem'],
            'messaging': ['Create the extraordinary', 'Immersive entertainment'],
            'weaknesses': ['Premium cost', 'Fragmented product messaging']
        },
        'Panasonic': {
            'website': 'https://www.panasonic.com',
            'features': ['Home appliances', 'Electronics', 'Image sensing', 'Smart home'],
            'messaging': ['A better life, a better world', 'Reliable household tech'],
            'weaknesses': ['Lower mindshare', 'Less aggressive marketing']
        },
        'Philips': {
            'website': 'https://www.philips.com',
            'features': ['Health tech', 'Personal care', 'Home electronics', 'Lighting'],
            'messaging': ['Innovation and you', 'Better care for more people'],
            'weaknesses': ['Broad category span', 'Premium perception challenges']
        },
        'TCL': {
            'website': 'https://www.tcl.com',
            'features': ['TVs', 'Smart home', 'Mobile devices', 'Value pricing'],
            'messaging': ['Inspire greatness', 'Quality entertainment at value'],
            'weaknesses': ['Brand trust', 'Lower premium perception']
        }
    },
    'general_b2b': {
        'Salesforce': {
            'website': 'https://www.salesforce.com',
            'features': ['CRM', 'Automation', 'Analytics', 'AI'],
            'messaging': ['Customer success platform', 'AI + CRM'],
            'weaknesses': ['Complexity', 'Price', 'Implementation cost']
        },
        'HubSpot': {
            'website': 'https://www.hubspot.com',
            'features': ['CRM', 'Marketing automation', 'Content tools'],
            'messaging': ['Grow better', 'All-in-one customer platform'],
            'weaknesses': ['Pricing scales quickly', 'Feature sprawl']
        },
        'Pipedrive': {
            'website': 'https://www.pipedrive.com',
            'features': ['Pipeline CRM', 'Sales automation', 'Reporting'],
            'messaging': ['The easy and effective CRM', 'Built for sales teams'],
            'weaknesses': ['Limited enterprise depth', 'Fewer marketing features']
        },
        'Zoho': {
            'website': 'https://www.zoho.com',
            'features': ['Business suite', 'CRM', 'Ops tools', 'Automation'],
            'messaging': ['Run your entire business'],
            'weaknesses': ['UI consistency', 'Learning curve across suite']
        },
        'Microsoft 365 Copilot': {
            'website': 'https://www.microsoft.com/en-us/microsoft-365/copilot',
            'features': ['Copilot', 'Teams', 'Office apps', 'OneDrive', 'Outlook'],
            'messaging': ['AI inside Microsoft 365', 'Enterprise integration', 'Connected productivity'],
            'weaknesses': ['Complex suite pricing', 'Enterprise overhead', 'Learning curve']
        },
        'Freshworks': {
            'website': 'https://www.freshworks.com',
            'features': ['Customer service', 'CRM', 'IT tools', 'Automation'],
            'messaging': ['Fresh approach to business software', 'Unified customer and employee tools'],
            'weaknesses': ['Less category dominance', 'Suite breadth vs depth tradeoff']
        },
        'SAP': {
            'website': 'https://www.sap.com',
            'features': ['ERP', 'CRM', 'Analytics', 'Business automation'],
            'messaging': ['The intelligent enterprise', 'Business software at scale'],
            'weaknesses': ['Complex implementation', 'Enterprise overhead']
        }
    }
}

BRAND_CATEGORY_HINTS = {
    'shopify': 'ecommerce',
    'bigcommerce': 'ecommerce',
    'woocomerce': 'ecommerce',
    'woocommerce': 'ecommerce',
    'wix': 'ecommerce',
    'squarespace': 'ecommerce',
    'notion': 'productivity',
    'coda': 'productivity',
    'asana': 'productivity',
    'clickup': 'productivity',
    'monday': 'productivity',
    'monday.com': 'productivity',
    'trello': 'productivity',
    'wrike': 'productivity',
    'airtable': 'productivity',
    'obsidian': 'productivity',
    'confluence': 'productivity',
    'google workspace': 'productivity',
    'microsoft 365': 'productivity',
    'microsoft': 'productivity',
    'copilot': 'general_b2b',
    'lg': 'electronics',
    'tv': 'electronics',
    'television': 'electronics',
    'appliance': 'electronics',
    'home theater': 'electronics',
    'electronics': 'electronics',
    'nike': 'sportswear',
    'adidas': 'sportswear',
    'puma': 'sportswear',
    'under armour': 'sportswear',
    'new balance': 'sportswear',
    'reebok': 'sportswear',
    'coca-cola': 'beverages',
    'coke': 'beverages',
    'limca': 'beverages',
    'thums up': 'beverages',
    'thumsup': 'beverages',
    '7up': 'beverages',
    'lg': 'electronics',
    'samsung': 'electronics',
    'sony': 'electronics',
    'panasonic': 'electronics',
    'philips': 'electronics',
    'hisense': 'electronics',
    'tcl': 'electronics',
    'sharp': 'electronics',
    'pepsi': 'beverages',
    'sprite': 'beverages',
    'dr pepper': 'beverages',
    'fanta': 'beverages',
    'mountain dew': 'beverages',
    'canva': 'productivity',
    'figma': 'productivity',
    'slack': 'productivity',
    'zoom': 'productivity',
    'airbnb': 'general_b2b',
    'uber': 'general_b2b',
    'amazon': 'ecommerce',
    'flipkart': 'ecommerce',
    'myntra': 'ecommerce',
    'zomato': 'general_b2b',
    'swiggy': 'general_b2b',
    'spotify': 'general_b2b',
    'netflix': 'general_b2b',
    'salesforce': 'general_b2b',
    'hubspot': 'general_b2b',
    'pipedrive': 'general_b2b',
    'zoho': 'general_b2b'
}

BRAND_COMPETITOR_OVERRIDES = {
    'notion': ['Coda', 'ClickUp', 'Airtable', 'Obsidian', 'Confluence', 'Google Workspace'],
    'coda': ['Notion', 'ClickUp', 'Airtable', 'Confluence', 'Google Workspace', 'Slack'],
    'clickup': ['Notion', 'Coda', 'Airtable', 'Confluence', 'Google Workspace', 'Slack'],
    'airtable': ['Notion', 'Coda', 'ClickUp', 'Confluence', 'Google Workspace', 'Slack'],
    'obsidian': ['Notion', 'Coda', 'Confluence', 'Google Workspace', 'Airtable', 'Slack'],
    'confluence': ['Notion', 'Coda', 'ClickUp', 'Airtable', 'Google Workspace', 'Slack'],
    'google workspace': ['Notion', 'Confluence', 'Coda', 'ClickUp', 'Airtable', 'Slack'],
    'limca': ['Sprite', '7Up', 'Mountain Dew', 'Fanta', 'Thums Up', 'Coca-Cola'],
    'coca-cola': ['Pepsi', 'Sprite', 'Fanta', 'Thums Up', 'Mountain Dew', '7Up'],
    'coke': ['Pepsi', 'Sprite', 'Fanta', 'Thums Up', 'Mountain Dew', '7Up'],
    'pepsi': ['Coca-Cola', 'Sprite', 'Fanta', 'Thums Up', 'Mountain Dew', '7Up'],
    'sprite': ['Pepsi', '7Up', 'Limca', 'Fanta', 'Mountain Dew', 'Coca-Cola'],
    'lg': ['Samsung', 'Sony', 'Panasonic', 'Philips', 'TCL', 'Hisense'],
    'samsung': ['LG', 'Sony', 'Panasonic', 'Philips', 'TCL', 'Hisense'],
    'nike': ['Adidas', 'Puma', 'Under Armour', 'New Balance', 'Reebok', 'ASICS'],
    'adidas': ['Nike', 'Puma', 'Under Armour', 'New Balance', 'Reebok', 'ASICS'],
    'shopify': ['BigCommerce', 'Adobe Commerce', 'WooCommerce', 'Squarespace', 'Wix', 'PrestaShop'],
    'canva': ['Figma', 'Adobe Express', 'Piktochart', 'VistaCreate', 'Visme', 'Miro'],
    'figma': ['Canva', 'Adobe XD', 'Sketch', 'Framer', 'Penpot', 'Miro'],
    'slack': ['Microsoft Teams', 'Google Chat', 'Zoom Team Chat', 'Discord', 'Mattermost', 'Notion']
}

# Supplemental profiles for competitors referenced in overrides/default lists.
EXTRA_COMPETITOR_PROFILES = {
    '7Up': {
        'website': 'https://www.7up.com',
        'features': ['Lemon-lime soda', 'Refreshment variants', 'Mixer usage'],
        'messaging': ['Cool and crisp refreshment', 'Light citrus profile'],
        'weaknesses': ['Smaller portfolio breadth', 'Lower differentiation']
    },
    'Thums Up': {
        'website': 'https://www.coca-cola.com/in/en/brands/thums-up',
        'features': ['Cola variant', 'Strong flavor profile', 'Local market focus'],
        'messaging': ['Strong taste identity', 'Bold refreshment'],
        'weaknesses': ['Regional concentration', 'Limited global expansion']
    },
    'Microsoft Teams': {
        'website': 'https://www.microsoft.com/microsoft-teams',
        'features': ['Chat', 'Meetings', 'Collaboration', 'File integration'],
        'messaging': ['Meet, chat, and collaborate', 'Enterprise communication'],
        'weaknesses': ['Suite complexity', 'Navigation overhead']
    },
    'Google Chat': {
        'website': 'https://workspace.google.com/products/chat/',
        'features': ['Team chat', 'Spaces', 'Google Workspace integration'],
        'messaging': ['Built-in collaboration', 'Workspace-native chat'],
        'weaknesses': ['Less standalone depth', 'Limited enterprise customization']
    },
    'Zoom Team Chat': {
        'website': 'https://www.zoom.com/en/products/team-chat/',
        'features': ['Team messaging', 'Meetings integration', 'Channels'],
        'messaging': ['Unified communications', 'Chat + meetings workflow'],
        'weaknesses': ['Platform sprawl risk', 'Less PM depth']
    },
    'Discord': {
        'website': 'https://discord.com',
        'features': ['Channels', 'Voice rooms', 'Communities', 'Integrations'],
        'messaging': ['Create space for your community', 'Real-time interaction'],
        'weaknesses': ['Enterprise governance limits', 'Informal perception']
    },
    'Mattermost': {
        'website': 'https://mattermost.com',
        'features': ['Self-hosted chat', 'Workflows', 'Enterprise control'],
        'messaging': ['Secure collaboration', 'Operational workflows'],
        'weaknesses': ['Smaller ecosystem', 'Setup complexity']
    },
    'Adobe Express': {
        'website': 'https://www.adobe.com/express/',
        'features': ['Templates', 'Quick design', 'Content creation', 'AI tools'],
        'messaging': ['Create standout content fast', 'Design for everyone'],
        'weaknesses': ['Depth limits for power users', 'Suite dependency']
    },
    'Piktochart': {
        'website': 'https://piktochart.com',
        'features': ['Infographics', 'Presentations', 'Visual reports'],
        'messaging': ['Visual storytelling made easy', 'Data-to-design workflows'],
        'weaknesses': ['Narrow use-case focus', 'Smaller brand pull']
    },
    'VistaCreate': {
        'website': 'https://create.vista.com',
        'features': ['Templates', 'Social creatives', 'Brand kit'],
        'messaging': ['Fast visual creation', 'Design made simple'],
        'weaknesses': ['Lower enterprise adoption', 'Limited advanced controls']
    },
    'Visme': {
        'website': 'https://www.visme.co',
        'features': ['Presentations', 'Infographics', 'Reports', 'Templates'],
        'messaging': ['Create visual content', 'Data storytelling at scale'],
        'weaknesses': ['Learning curve for advanced use', 'Template similarity']
    },
    'Adobe XD': {
        'website': 'https://www.adobe.com/products/xd.html',
        'features': ['UI/UX design', 'Prototyping', 'Design systems'],
        'messaging': ['Design and prototype experiences', 'Collaborative UX workflows'],
        'weaknesses': ['Product uncertainty', 'Slower momentum']
    },
    'Sketch': {
        'website': 'https://www.sketch.com',
        'features': ['Interface design', 'Prototyping', 'Libraries'],
        'messaging': ['Design toolkit for teams', 'Craft digital products'],
        'weaknesses': ['Platform limitations', 'Collaboration depth']
    },
    'Framer': {
        'website': 'https://www.framer.com',
        'features': ['Interactive prototyping', 'Website publishing', 'Design workflows'],
        'messaging': ['Design and publish modern sites', 'From idea to live experience'],
        'weaknesses': ['Steeper workflow for non-designers', 'Niche focus']
    },
    'Penpot': {
        'website': 'https://penpot.app',
        'features': ['Open-source UI design', 'Prototyping', 'Team collaboration'],
        'messaging': ['Open-source design and prototyping', 'Design freedom for teams'],
        'weaknesses': ['Smaller ecosystem', 'Feature maturity gap']
    },
    'Miro': {
        'website': 'https://miro.com',
        'features': ['Whiteboarding', 'Workshops', 'Collaboration templates'],
        'messaging': ['Innovation workspace', 'Collaborate visually at scale'],
        'weaknesses': ['Board sprawl', 'Governance challenges']
    }
}

CATEGORY_DEFAULT_COMPETITORS = {
    'productivity': ['Notion', 'Coda', 'ClickUp', 'Airtable', 'Obsidian', 'Confluence', 'Google Workspace', 'Slack', 'Asana', 'Trello'],
    'ecommerce': ['Shopify', 'BigCommerce', 'Adobe Commerce', 'WooCommerce', 'Squarespace', 'Wix', 'PrestaShop', 'Ecwid', 'OpenCart'],
    'sportswear': ['Nike', 'Adidas', 'Puma', 'Under Armour', 'New Balance', 'Reebok', 'ASICS', 'Skechers', 'Lululemon'],
    'electronics': ['LG', 'Samsung', 'Sony', 'Panasonic', 'Philips', 'TCL', 'Hisense', 'Xiaomi', 'Haier'],
    'beverages': ['Coca-Cola', 'Pepsi', 'Sprite', 'Fanta', 'Mountain Dew', '7Up', 'Thums Up', 'Mirinda', 'Dr Pepper'],
    'general_b2b': ['Salesforce', 'HubSpot', 'Pipedrive', 'Zoho', 'Microsoft 365 Copilot', 'Freshworks', 'SAP', 'Oracle', 'ServiceNow']
}


class IntelligenceEngine:
    """Core intelligence engine for competitive analysis"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.web_scraper = WebScraperService()
        self.guardrails_service = GuardrailsService(self.llm_service)
        self.default_competitors = self._build_flat_competitor_index()

    def _build_flat_competitor_index(self) -> Dict[str, Dict[str, Any]]:
        """Flatten all category catalogs into a single lookup table."""
        flat_index: Dict[str, Dict[str, Any]] = {}
        for category_profiles in CATEGORY_COMPETITORS.values():
            flat_index.update(category_profiles)
        flat_index.update(EXTRA_COMPETITOR_PROFILES)
        return flat_index
    
    def analyze_brand(self, brand_name: str, competitor_limit: int = 8) -> Dict[str, Any]:
        """Analyze a brand with its competitive landscape"""
        logger.info(f"Starting analysis for brand: {brand_name}")
        category = self._detect_category(brand_name)
        safe_limit = max(1, min(int(competitor_limit or 8), 12))
        
        # Identify competitors
        competitors_to_analyze, guardrail_audit = self._identify_competitors_with_guardrails(
            brand_name,
            limit=safe_limit,
        )
        
        # Gather data on each competitor
        competitor_data_list = []
        for competitor_name in competitors_to_analyze:
            try:
                competitor_data = self._analyze_single_competitor(brand_name, competitor_name)
            except Exception as comp_exc:
                logger.error(f"Failed competitor analysis for {competitor_name}: {comp_exc}")
                competitor_data = {
                    'competitor_name': competitor_name,
                    'website': '',
                    'insights': self.llm_service._build_fallback_insights(
                        competitor_name,
                        {
                            'category': category,
                            'default_features': [],
                            'default_messaging': [],
                            'default_weaknesses': [],
                        }
                    ),
                    'threat_level': 'medium',
                    'market_position': 'challenger',
                    'signals': [],
                    'sources_used': [],
                    'error': str(comp_exc)
                }
            competitor_data_list.append(competitor_data)
        
        # Generate market positioning analysis
        market_analysis = self.llm_service.analyze_market_positioning(brand_name, competitor_data_list, category)
        
        # Generate campaign recommendations
        campaign_recs = self.llm_service.generate_campaign_recommendations(brand_name, competitor_data_list, category)
        
        # Compile full report
        report = {
            'brand_name': brand_name,
            'analyzed_at': datetime.utcnow().isoformat(),
            'competitors_analyzed': len(competitor_data_list),
            'competitor_data': competitor_data_list,
            'market_analysis': market_analysis,
            'campaign_recommendations': campaign_recs,
            'signals_extracted': sum(len(c.get('signals', [])) for c in competitor_data_list),
            'guardrails': guardrail_audit
        }
        
        return report
    
    def _identify_competitors(self, brand_name: str, limit: int = 8) -> List[str]:
        """Compatibility wrapper that returns only competitor names."""
        names, _audit = self._identify_competitors_with_guardrails(brand_name, limit)
        return names

    def _identify_competitors_with_guardrails(self, brand_name: str, limit: int = 8) -> Any:
        """Identify top competitors for a brand using dynamic discovery first, then fallbacks."""
        category = self._detect_category(brand_name)
        candidate_pool: List[str] = []
        competitor_names: List[str] = []

        def append_unique(candidates: List[str]):
            for candidate in candidates or []:
                clean_name = (candidate or '').strip()
                if not clean_name:
                    continue
                if clean_name not in candidate_pool:
                    candidate_pool.append(clean_name)
                if len(candidate_pool) >= max(limit * 3, limit):
                    return

        # 1) Dynamic discovery from LLM (category-aware)
        discovered = self.llm_service.discover_competitors(brand_name, category, limit)
        append_unique(discovered)

        # 2) Retry discovery without strict category constraint for unfamiliar brands.
        if len(discovered) < max(3, limit // 2):
            append_unique(self.llm_service.discover_competitors(brand_name, 'auto', limit))

        # 3) Category catalog fallback
        if len(candidate_pool) < limit:
            competitor_profiles = self._get_competitor_profiles(category)
            append_unique(list(competitor_profiles.keys()))

        # 4) Category defaults + generic fallback
        if len(candidate_pool) < limit:
            append_unique(CATEGORY_DEFAULT_COMPETITORS.get(category, []))
        if len(candidate_pool) < limit:
            generic_fallback = self._get_competitor_profiles('general_b2b')
            append_unique(list(generic_fallback.keys()))
        if len(candidate_pool) < limit:
            append_unique(CATEGORY_DEFAULT_COMPETITORS.get('general_b2b', []))

        validation_category = category if category != 'general_b2b' else 'auto'
        guardrail_audit = self.guardrails_service.evaluate_competitors(
            brand_name=brand_name,
            category=validation_category,
            candidates=candidate_pool,
            limit=limit,
        )

        for candidate_name in guardrail_audit.get('approved_competitors', []):
            if self._is_valid_competitor_name(brand_name, candidate_name) and candidate_name not in competitor_names:
                competitor_names.append(candidate_name)
            if len(competitor_names) >= limit:
                break

        # Safety net: if guardrails over-filter, keep deterministic valid candidates.
        if len(competitor_names) < limit:
            for candidate_name in candidate_pool:
                if self._is_valid_competitor_name(brand_name, candidate_name) and candidate_name not in competitor_names:
                    competitor_names.append(candidate_name)
                if len(competitor_names) >= limit:
                    break

        guardrail_audit['final_selected_competitors'] = competitor_names[:limit]
        return competitor_names[:limit], guardrail_audit

    def _is_valid_competitor_name(self, brand_name: str, competitor_name: str) -> bool:
        """Deterministic guardrails to reject clearly invalid competitor names."""
        brand_norm = brand_name.strip().lower()
        comp_norm = competitor_name.strip().lower()

        if not comp_norm or len(comp_norm) < 2:
            return False
        if comp_norm == brand_norm:
            return False
        if comp_norm in {'unknown', 'n/a', 'none', 'null', 'competitor', 'brand'}:
            return False
        if any(token in comp_norm for token in ['http://', 'https://', '.com/', '/pricing']):
            return False
        return True

    def _detect_category(self, brand_name: str) -> str:
        """Detect a likely market category for the brand."""
        normalized = brand_name.strip().lower()

        for hint, category in BRAND_CATEGORY_HINTS.items():
            if hint in normalized:
                return category

        keyword_map = {
            'store': 'ecommerce',
            'shop': 'ecommerce',
            'commerce': 'ecommerce',
            'marketplace': 'ecommerce',
            'task': 'productivity',
            'project': 'productivity',
            'workspace': 'productivity',
            'collaboration': 'productivity',
            'design': 'productivity',
            'creative': 'productivity',
            'content': 'productivity',
            'video': 'productivity',
            'photo': 'productivity',
            'marketing': 'general_b2b',
            'crm': 'general_b2b',
            'sales': 'general_b2b',
            'apparel': 'sportswear',
            'shoe': 'sportswear',
            'wear': 'sportswear',
            'drink': 'beverages',
            'beverage': 'beverages',
            'soda': 'beverages',
            'juice': 'beverages',
            'cola': 'beverages',
            'soft drink': 'beverages'
        }
        for keyword, category in keyword_map.items():
            if keyword in normalized:
                return category

        # LLM fallback for unfamiliar brands so the competitor set isn't always the same.
        try:
            self.llm_service._ensure_initialized()
            prompt = f"""
Classify the brand '{brand_name}' into exactly one of these categories:
productivity, ecommerce, sportswear, beverages, general_b2b.

Return only valid JSON in this exact format:
{{"category":"<one of the allowed categories>"}}
"""
            response = self.llm_service.model.generate_content(prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            parsed = json.loads(text)
            category = parsed.get('category', 'general_b2b').strip().lower()
            if category in CATEGORY_COMPETITORS:
                return category
        except Exception as exc:
            logger.warning(f"Category detection fallback used for {brand_name}: {exc}")

        return 'general_b2b'

    def _get_competitor_profiles(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Return competitor profiles for the given category."""
        profiles = CATEGORY_COMPETITORS.get(category, {})
        if profiles:
            return profiles
        return CATEGORY_COMPETITORS['general_b2b']
    
    def _analyze_single_competitor(self, brand_name: str, competitor_name: str) -> Dict[str, Any]:
        """Analyze a single competitor"""
        logger.info(f"Analyzing competitor: {competitor_name}")
        
        # Get competitor data
        category = self._detect_category(brand_name)
        competitor_info = self._get_competitor_profiles(category).get(
            competitor_name,
            self.default_competitors.get(competitor_name, {})
        )
        if not competitor_info:
            competitor_info = self._build_synthetic_competitor_profile(competitor_name, category)

        # Dynamic enrichment: try to infer a likely official website when missing.
        if not competitor_info.get('website'):
            inferred_website = self.llm_service.discover_company_website(competitor_name, category)
            if inferred_website:
                competitor_info['website'] = inferred_website
        
        # Scrape web data
        website = competitor_info.get('website', '')
        if website:
            web_data = self.web_scraper.aggregate_competitor_data(competitor_name, website)
        else:
            web_data = {}
        
        # Prepare data for LLM analysis
        raw_data = {
            'competitor_name': competitor_name,
            'website': website,
            'category': category,
            'default_features': competitor_info.get('features', []),
            'default_messaging': competitor_info.get('messaging', []),
            'default_weaknesses': competitor_info.get('weaknesses', []),
            'web_data': web_data
        }
        
        # Extract insights using LLM
        insights = self.llm_service.extract_competitor_insights(competitor_name, raw_data)
        
        # Compile competitor analysis
        competitive_threats = insights.get('competitive_threats', [])
        position_label = 'challenger'
        if isinstance(competitive_threats, list) and len(competitive_threats) >= 3:
            position_label = 'strong_competitor'

        competitor_analysis = {
            'competitor_name': competitor_name,
            'website': website,
            'insights': insights,
            'threat_level': self._calculate_threat_level(insights),
            'market_position': position_label,
            'signals': self._extract_signals(competitor_name, insights),
            'sources_used': web_data.get('sources', [])
        }
        
        return competitor_analysis

    def _build_synthetic_competitor_profile(self, competitor_name: str, category: str) -> Dict[str, Any]:
        """Build a generic profile when we only know the competitor name."""
        return {
            'website': '',
            'features': [f'{competitor_name} core platform', 'Automation', 'Reporting', 'Collaboration'],
            'messaging': [f'{competitor_name} positions itself as a category leader', 'Fast adoption', 'Outcome focus'],
            'weaknesses': ['Potential complexity', 'Pricing pressure', 'Competitive overlap']
        }
    
    def _calculate_threat_level(self, insights: Dict) -> str:
        """Calculate threat level based on insights"""
        # Simplified threat calculation
        competitive_threats = len(insights.get('competitive_threats', []))
        
        if competitive_threats >= 3:
            return 'high'
        elif competitive_threats >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _extract_signals(self, competitor_name: str, insights: Dict) -> List[Dict]:
        """Extract individual signals from insights"""
        signals = []
        
        # Extract feature signals
        for feature in insights.get('key_features', [])[:3]:
            signals.append({
                'type': 'feature',
                'text': feature,
                'sentiment': 'neutral',
                'relevance': 0.8
            })
        
        # Extract weakness signals
        for weakness in insights.get('market_gaps', [])[:3]:
            signals.append({
                'type': 'weakness',
                'text': weakness,
                'sentiment': 'negative',
                'relevance': 0.9
            })
        
        # Extract opportunity signals
        for opportunity in insights.get('opportunity_areas', [])[:2]:
            signals.append({
                'type': 'opportunity',
                'text': opportunity,
                'sentiment': 'positive',
                'relevance': 0.7
            })
        
        return signals
    
    def save_analysis_to_db(self, brand_name: str, report: Dict[str, Any]) -> str:
        """Save analysis results to database"""
        try:
            detected_category = self._detect_category(brand_name)
            category_profile = {
                'productivity': ('Productivity Software', 'Productivity'),
                'ecommerce': ('Ecommerce Platform', 'Commerce'),
                'sportswear': ('Sportswear and Apparel', 'Consumer'),
                'electronics': ('Consumer Electronics', 'Consumer'),
                'beverages': ('Beverages and FMCG', 'Consumer'),
                'general_b2b': ('B2B Software', 'Business')
            }.get(detected_category, ('Business', 'Business'))

            # Create or get brand
            brand = Brand.query.filter_by(name=brand_name).first()
            if not brand:
                brand = Brand(
                    name=brand_name,
                    industry=category_profile[0],
                    market_segment=category_profile[1]
                )
                db.session.add(brand)
                db.session.flush()  # Flush to get the ID
            else:
                brand.industry = category_profile[0]
                brand.market_segment = category_profile[1]
                db.session.add(brand)
            
            # Save competitor analyses
            for comp_data in report.get('competitor_data', []):
                comp_analysis = CompetitorAnalysis(
                    brand_id=brand.id,
                    competitor_name=comp_data.get('competitor_name')
                )
                
                # Set JSON fields
                comp_analysis.set_json('features', comp_data.get('insights', {}).get('key_features', []))
                comp_analysis.set_json('messaging', comp_data.get('insights', {}).get('messaging_themes', []))
                comp_analysis.set_json('customer_sentiment', comp_data.get('insights', {}).get('customer_sentiment', {}))
                comp_analysis.set_json('pricing', comp_data.get('insights', {}).get('pricing_strategy', {}))
                comp_analysis.set_json('weaknesses', comp_data.get('insights', {}).get('market_gaps', []))
                comp_analysis.set_json('sources', comp_data.get('sources_used', []))
                
                comp_analysis.threat_level = comp_data.get('threat_level', 'medium')
                comp_analysis.market_position = comp_data.get('market_position', 'competitor')
                
                db.session.add(comp_analysis)
            
            db.session.commit()
            logger.info(f"Saved analysis for {brand_name} with ID: {brand.id}")
            return brand.id
        
        except Exception as e:
            logger.error(f"Error saving analysis to DB: {e}")
            db.session.rollback()
            raise
    
    def get_comparative_insights(self, brand_id: str) -> Dict[str, Any]:
        """Get comparative insights for a brand"""
        brand = Brand.query.get(brand_id)
        if not brand:
            return {}
        
        competitors = CompetitorAnalysis.query.filter_by(brand_id=brand_id).all()
        
        insights = {
            'brand_name': brand.name,
            'total_competitors_analyzed': len(competitors),
            'competitors': [c.to_dict() for c in competitors]
        }
        
        return insights
