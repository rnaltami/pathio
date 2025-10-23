from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Curated database of AI tools
AI_TOOLS_DATABASE = {
    "Writing & Content": [
        {
            "name": "ChatGPT",
            "description": "Advanced conversational AI for writing, brainstorming, and content creation",
            "pricing": "Freemium",
            "website": "https://chat.openai.com",
            "features": ["AI Writing", "Brainstorming", "Editing", "Translation"],
            "rating": 4.8
        },
        {
            "name": "Claude",
            "description": "AI assistant with strong writing capabilities and document analysis",
            "pricing": "Freemium",
            "website": "https://claude.ai",
            "features": ["AI Writing", "Document Analysis", "Code Review", "Creative Writing"],
            "rating": 4.7
        },
        {
            "name": "Jasper",
            "description": "AI copywriting tool for marketing content, blogs, and social media",
            "pricing": "Paid",
            "website": "https://jasper.ai",
            "features": ["Marketing Copy", "Blog Writing", "Social Media", "SEO Content"],
            "rating": 4.5
        },
        {
            "name": "Copy.ai",
            "description": "AI-powered copywriting for ads, emails, and marketing materials",
            "pricing": "Freemium",
            "website": "https://copy.ai",
            "features": ["Ad Copy", "Email Marketing", "Product Descriptions", "Templates"],
            "rating": 4.4
        },
        {
            "name": "Writesonic",
            "description": "AI writing assistant for blogs, ads, and long-form content",
            "pricing": "Freemium",
            "website": "https://writesonic.com",
            "features": ["Blog Writing", "Ad Copy", "Long-form Content", "SEO"],
            "rating": 4.3
        },
        {
            "name": "Grammarly",
            "description": "AI-powered writing assistant for grammar, style, and clarity",
            "pricing": "Freemium",
            "website": "https://grammarly.com",
            "features": ["Grammar Check", "Style Suggestions", "Tone Detection", "Plagiarism Check"],
            "rating": 4.6
        },
        {
            "name": "Notion AI",
            "description": "AI assistant integrated into Notion for writing and organization",
            "pricing": "Paid",
            "website": "https://notion.so",
            "features": ["Note Taking", "Summarization", "Brainstorming", "Organization"],
            "rating": 4.4
        },
        {
            "name": "Sudowrite",
            "description": "AI writing tool specifically designed for fiction and creative writing",
            "pricing": "Paid",
            "website": "https://sudowrite.com",
            "features": ["Fiction Writing", "Character Development", "Plot Generation", "Style Transfer"],
            "rating": 4.5
        }
    ],
    "Design & Creative": [
        {
            "name": "Midjourney",
            "description": "AI image generation tool known for artistic and creative visuals",
            "pricing": "Paid",
            "website": "https://midjourney.com",
            "features": ["Image Generation", "Artistic Styles", "Character Creation", "High Quality"],
            "rating": 4.8
        },
        {
            "name": "DALL-E 3",
            "description": "OpenAI's advanced image generation with high detail and accuracy",
            "pricing": "Paid",
            "website": "https://openai.com/dall-e-3",
            "features": ["Image Generation", "Text-to-Image", "High Detail", "Creative Control"],
            "rating": 4.7
        },
        {
            "name": "Stable Diffusion",
            "description": "Open-source AI image generation with extensive customization",
            "pricing": "Freemium",
            "website": "https://stability.ai",
            "features": ["Open Source", "Custom Models", "Local Generation", "Extensible"],
            "rating": 4.5
        },
        {
            "name": "Adobe Firefly",
            "description": "Adobe's AI creative tools integrated into Creative Cloud",
            "pricing": "Paid",
            "website": "https://adobe.com/firefly",
            "features": ["Creative Cloud Integration", "Professional Tools", "Brand Safety", "Commercial Use"],
            "rating": 4.4
        },
        {
            "name": "Canva AI",
            "description": "AI-powered design tool for quick graphics and presentations",
            "pricing": "Freemium",
            "website": "https://canva.com",
            "features": ["Templates", "AI Design", "Collaboration", "Brand Kit"],
            "rating": 4.6
        },
        {
            "name": "Leonardo AI",
            "description": "AI art platform with character consistency and style control",
            "pricing": "Freemium",
            "website": "https://leonardo.ai",
            "features": ["Character Consistency", "Style Control", "Batch Generation", "API Access"],
            "rating": 4.5
        },
        {
            "name": "Runway",
            "description": "AI video and image generation with advanced editing capabilities",
            "pricing": "Freemium",
            "website": "https://runwayml.com",
            "features": ["Video Generation", "Image Editing", "Motion Graphics", "Professional Tools"],
            "rating": 4.4
        }
    ],
    "Coding & Development": [
        {
            "name": "GitHub Copilot",
            "description": "AI pair programmer that suggests code as you type",
            "pricing": "Paid",
            "website": "https://github.com/features/copilot",
            "features": ["Code Completion", "Multi-language", "IDE Integration", "Context Aware"],
            "rating": 4.6
        },
        {
            "name": "ChatGPT",
            "description": "Versatile AI assistant for coding help, debugging, and code review",
            "pricing": "Freemium",
            "website": "https://chat.openai.com",
            "features": ["Code Generation", "Debugging", "Code Review", "Documentation"],
            "rating": 4.7
        },
        {
            "name": "Claude",
            "description": "AI assistant with strong coding capabilities and large context window",
            "pricing": "Freemium",
            "website": "https://claude.ai",
            "features": ["Code Analysis", "Large Context", "Code Review", "Architecture Design"],
            "rating": 4.8
        },
        {
            "name": "Cursor",
            "description": "AI-powered code editor built for pair programming with AI",
            "pricing": "Freemium",
            "website": "https://cursor.sh",
            "features": ["AI Editor", "Code Generation", "Refactoring", "Multi-file Context"],
            "rating": 4.5
        },
        {
            "name": "Replit",
            "description": "Online IDE with AI coding assistant and collaboration features",
            "pricing": "Freemium",
            "website": "https://replit.com",
            "features": ["Online IDE", "AI Assistant", "Collaboration", "Deployment"],
            "rating": 4.3
        },
        {
            "name": "Tabnine",
            "description": "AI code completion tool supporting multiple languages and IDEs",
            "pricing": "Freemium",
            "website": "https://tabnine.com",
            "features": ["Code Completion", "Multi-language", "IDE Support", "Team Features"],
            "rating": 4.2
        },
        {
            "name": "Codeium",
            "description": "Free AI code completion and chat assistant for developers",
            "pricing": "Free",
            "website": "https://codeium.com",
            "features": ["Free Tier", "Code Completion", "AI Chat", "Multi-language"],
            "rating": 4.4
        },
        {
            "name": "GitHub Codespaces",
            "description": "Cloud-based development environment with AI-powered coding assistance",
            "pricing": "Freemium",
            "website": "https://github.com/features/codespaces",
            "features": ["Cloud IDE", "AI Coding", "Collaboration", "Pre-configured Environments"],
            "rating": 4.3
        },
        {
            "name": "Amazon CodeWhisperer",
            "description": "AI code generator that provides real-time code suggestions",
            "pricing": "Freemium",
            "website": "https://aws.amazon.com/codewhisperer",
            "features": ["Code Generation", "Security Scanning", "Multi-language", "AWS Integration"],
            "rating": 4.1
        },
        {
            "name": "DeepCode",
            "description": "AI-powered code review and bug detection platform",
            "pricing": "Freemium",
            "website": "https://deepcode.ai",
            "features": ["Code Review", "Bug Detection", "Security Analysis", "Multi-language"],
            "rating": 4.0
        },
        {
            "name": "Kite",
            "description": "AI-powered code completion with intelligent suggestions",
            "pricing": "Freemium",
            "website": "https://kite.com",
            "features": ["Code Completion", "Documentation", "Multi-language", "IDE Integration"],
            "rating": 4.2
        },
        {
            "name": "IntelliCode",
            "description": "Microsoft's AI-assisted development tool for Visual Studio",
            "pricing": "Free",
            "website": "https://visualstudio.microsoft.com/services/intellicode",
            "features": ["Code Completion", "Visual Studio Integration", "Team Learning", "Multi-language"],
            "rating": 4.3
        }
    ],
    "Marketing & SEO": [
        {
            "name": "Jasper",
            "description": "AI marketing platform for content creation and campaign management",
            "pricing": "Paid",
            "website": "https://jasper.ai",
            "features": ["Marketing Copy", "Campaign Management", "Brand Voice", "Templates"],
            "rating": 4.5
        },
        {
            "name": "Copy.ai",
            "description": "AI copywriting tool for ads, social media, and marketing content",
            "pricing": "Freemium",
            "website": "https://copy.ai",
            "features": ["Ad Copy", "Social Media", "Email Marketing", "A/B Testing"],
            "rating": 4.4
        },
        {
            "name": "Surfer SEO",
            "description": "AI-powered SEO tool for content optimization and keyword research",
            "pricing": "Paid",
            "website": "https://surferseo.com",
            "features": ["SEO Analysis", "Keyword Research", "Content Optimization", "Rank Tracking"],
            "rating": 4.3
        },
        {
            "name": "Frase",
            "description": "AI content optimization tool for SEO and content strategy",
            "pricing": "Paid",
            "website": "https://frase.io",
            "features": ["Content Research", "SEO Optimization", "Content Briefs", "Analytics"],
            "rating": 4.2
        }
    ],
    "Productivity & Business": [
        {
            "name": "Notion AI",
            "description": "AI assistant integrated into Notion for writing and organization",
            "pricing": "Paid",
            "website": "https://notion.so",
            "features": ["Note Taking", "Summarization", "Task Management", "Database Management"],
            "rating": 4.6
        },
        {
            "name": "Obsidian",
            "description": "Knowledge management tool with AI plugins for note-taking",
            "pricing": "Freemium",
            "website": "https://obsidian.md",
            "features": ["Knowledge Graph", "AI Plugins", "Local Storage", "Extensible"],
            "rating": 4.5
        },
        {
            "name": "Calendly",
            "description": "AI-powered scheduling tool with smart meeting coordination",
            "pricing": "Freemium",
            "website": "https://calendly.com",
            "features": ["Smart Scheduling", "Meeting Coordination", "Time Zone Handling", "Integrations"],
            "rating": 4.4
        },
        {
            "name": "Loom",
            "description": "AI-powered video messaging and screen recording tool",
            "pricing": "Freemium",
            "website": "https://loom.com",
            "features": ["Screen Recording", "AI Transcription", "Video Messaging", "Team Collaboration"],
            "rating": 4.3
        }
    ],
    "Data & Analytics": [
        {
            "name": "Tableau",
            "description": "AI-powered data visualization and business intelligence platform",
            "pricing": "Paid",
            "website": "https://tableau.com",
            "features": ["Data Visualization", "AI Insights", "Dashboard Creation", "Enterprise Features"],
            "rating": 4.5
        },
        {
            "name": "Power BI",
            "description": "Microsoft's AI-powered business analytics and data visualization",
            "pricing": "Freemium",
            "website": "https://powerbi.microsoft.com",
            "features": ["Data Visualization", "AI Insights", "Excel Integration", "Cloud Analytics"],
            "rating": 4.4
        },
        {
            "name": "DataRobot",
            "description": "AI platform for automated machine learning and data science",
            "pricing": "Paid",
            "website": "https://datarobot.com",
            "features": ["AutoML", "Model Deployment", "Data Science", "Enterprise AI"],
            "rating": 4.3
        }
    ]
}

class AIToolSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None

class AIToolSearchResponse(BaseModel):
    tools: List[Dict[str, Any]]
    total: int
    category: str
    search_query: str

def search_tools_in_database(query: str, category: str = None) -> List[Dict[str, Any]]:
    """Search for AI tools in the curated database with intelligent matching"""
    query_lower = query.lower()
    results = []
    
    # Define keyword mappings for better search
    keyword_mappings = {
        'coding': ['code', 'programming', 'development', 'coding', 'debugging', 'programmer', 'developer'],
        'writing': ['write', 'content', 'copy', 'blog', 'article', 'text', 'words'],
        'design': ['design', 'image', 'visual', 'art', 'creative', 'graphic', 'photo'],
        'marketing': ['marketing', 'seo', 'ad', 'campaign', 'social', 'promotion'],
        'productivity': ['productivity', 'task', 'management', 'organization', 'workflow'],
        'data': ['data', 'analytics', 'chart', 'visualization', 'insights', 'metrics'],
        'ai': ['ai', 'artificial', 'intelligence', 'machine', 'learning', 'automation'],
        'vibe': ['fun', 'creative', 'inspiring', 'cool', 'awesome', 'amazing', 'great']
    }
    
    # Expand query with related keywords
    expanded_query = [query_lower]
    for key, synonyms in keyword_mappings.items():
        if key in query_lower:
            expanded_query.extend(synonyms)
    
    # Determine which categories to search
    if category and category in AI_TOOLS_DATABASE:
        categories_to_search = [category]
    else:
        categories_to_search = list(AI_TOOLS_DATABASE.keys())
    
    for cat in categories_to_search:
        for tool in AI_TOOLS_DATABASE[cat]:
            # Search in tool name, description, and features
            searchable_text = f"{tool['name']} {tool['description']} {' '.join(tool['features'])}".lower()
            
            # Check if any expanded query word matches
            matches = 0
            for word in expanded_query:
                if word in searchable_text:
                    matches += 1
            
            # If we have matches, add the tool with a score
            if matches > 0:
                tool_with_category = tool.copy()
                tool_with_category['category'] = cat
                tool_with_category['match_score'] = matches
                results.append(tool_with_category)
    
    # Sort by match score (most relevant first)
    results.sort(key=lambda x: x['match_score'], reverse=True)
    
    # Remove duplicates based on tool name
    seen_names = set()
    unique_results = []
    for tool in results:
        if tool['name'].lower() not in seen_names:
            seen_names.add(tool['name'].lower())
            # Remove the match_score before returning
            del tool['match_score']
            unique_results.append(tool)
    
    return unique_results[:10]  # Limit to 10 results

@router.post("/ai-tools/search", response_model=AIToolSearchResponse)
async def search_ai_tools(request: AIToolSearchRequest):
    """Search for AI tools in the curated database"""
    
    try:
        # Search in the database
        tools = search_tools_in_database(request.query, request.category)
        
        return AIToolSearchResponse(
            tools=tools,
            total=len(tools),
            category=request.category or "General",
            search_query=request.query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI tools search failed: {str(e)}")

@router.get("/ai-tools/categories")
def get_categories():
    """Get available AI tool categories"""
    return {
        "categories": list(AI_TOOLS_DATABASE.keys()) + ["General"]
    }

@router.get("/ai-tools/health")
def ai_tools_health():
    """Check if AI tools service is working"""
    return {
        "status": "healthy",
        "database_tools": sum(len(tools) for tools in AI_TOOLS_DATABASE.values())
    }