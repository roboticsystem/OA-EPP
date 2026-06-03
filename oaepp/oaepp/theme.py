import reflex as rx

COLORS = {
    "gray.50": "#f9fafb",
    "gray.100": "#f3f4f6",
    "gray.200": "#e5e7eb",
    "gray.300": "#d1d5db",
    "gray.400": "#9ca3af",
    "gray.500": "#6b7280",
    "gray.600": "#4b5563",
    "gray.700": "#374151",
    "gray.800": "#1f2937",
    "blue.50": "#eff6ff",
    "blue.100": "#dbeafe",
    "blue.400": "#60a5fa",
    "blue.500": "#3b82f6",
    "blue.600": "#2563eb",
    "blue.700": "#1d4ed8",
    "green.400": "#4ade80",
    "green.500": "#22c55e",
    "green.600": "#16a34a",
    "purple.400": "#c084fc",
    "purple.600": "#9333ea",
    "orange.400": "#fb923c",
    "orange.500": "#f97316",
    "red.50": "#fef2f2",
    "red.100": "#fee2e2",
    "red.500": "#ef4444",
    "red.600": "#dc2626",
    "yellow.50": "#fefce8",
    "yellow.100": "#fef9c3",
    "yellow.500": "#eab308",
    "yellow.600": "#ca8a04",
}

FONT = "'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif"


def c(key: str) -> str:
    return COLORS.get(key, key)
