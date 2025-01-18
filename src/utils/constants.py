"""Constants used throughout the application."""

FEATURE_KEYWORDS = [
    "authentication",
    "authorization",
    "database",
    "api",
    "storage",
    "search",
    "analytics",
    "notifications",
    "real-time",
    "messaging",
    "payment",
    "social",
    "responsive",
    "accessibility"
]

COMPONENT_PATTERNS = {
    "navigation": [
        r"class=['\"].*?nav.*?['\"]",
        r"<nav.*?>",
        r"class=['\"].*?menu.*?['\"]"
    ],
    "form": [
        r"<form.*?>",
        r"class=['\"].*?form.*?['\"]",
        r"<input.*?>"
    ],
    "layout": [
        r"class=['\"].*?container.*?['\"]",
        r"class=['\"].*?grid.*?['\"]",
        r"class=['\"].*?flex.*?['\"]"
    ],
    "interactive": [
        r"<button.*?>",
        r"class=['\"].*?button.*?['\"]",
        r"<a.*?>"
    ]
} 