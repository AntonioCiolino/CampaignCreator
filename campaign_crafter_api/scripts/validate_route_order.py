#!/usr/bin/env python3
"""
Route Order Validation Script for Campaign Crafter API

This script validates that FastAPI routes are in the correct order to prevent
route conflicts where generic parameterized routes catch specific routes.

Usage: python scripts/validate_route_order.py
"""

import re
import sys
from pathlib import Path
from typing import List, Dict


class RouteInfo:
    def __init__(self, method: str, path: str, line_number: int, function_name: str):
        self.method = method
        self.path = path
        self.line_number = line_number
        self.function_name = function_name
        self.is_parameterized = "{" in path and "}" in path
        self.specificity_score = self._calculate_specificity()
    
    def _calculate_specificity(self) -> int:
        """Calculate route specificity score (higher = more specific)"""
        score = 0
        
        # Static path segments are more specific
        segments = self.path.strip("/").split("/")
        for segment in segments:
            if "{" not in segment:
                score += 10  # Static segment
            else:
                score -= 5   # Parameter segment
        
        # Longer paths are generally more specific
        score += len(segments)
        
        return score
    
    def __str__(self):
        return f"{self.method} {self.path} (line {self.line_number}, specificity: {self.specificity_score})"


def extract_routes_from_file(file_path: Path) -> List[RouteInfo]:
    """Extract all routes from a FastAPI router file"""
    routes = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    route_pattern = r'@router\.(get|post|put|delete|patch)\("([^"]+)"'
    function_pattern = r'(async )?def (\w+)\('
    
    for i, line in enumerate(lines, 1):
        route_match = re.search(route_pattern, line)
        if route_match:
            method = route_match.group(1).upper()
            path = route_match.group(2)
            
            # Find the function name on the next few lines
            function_name = "unknown"
            for j in range(i, min(i + 5, len(lines))):
                func_match = re.search(function_pattern, lines[j])
                if func_match:
                    function_name = func_match.group(2)
                    break
            
            routes.append(RouteInfo(method, path, i, function_name))
    
    return routes


def validate_route_order(routes: List[RouteInfo]) -> List[str]:
    """Validate that routes are in correct order and return any issues"""
    issues = []
    
    # Group routes by method
    routes_by_method = {}
    for route in routes:
        if route.method not in routes_by_method:
            routes_by_method[route.method] = []
        routes_by_method[route.method].append(route)
    
    for method, method_routes in routes_by_method.items():
        # Check for route conflicts within the same method
        for i, route in enumerate(method_routes):
            for j, other_route in enumerate(method_routes[i+1:], i+1):
                if would_conflict(route, other_route):
                    issues.append(
                        f"ROUTE CONFLICT in {route.function_name}:\n"
                        f"  Line {route.line_number}: {route.method} {route.path} (specificity: {route.specificity_score})\n"
                        f"  Line {other_route.line_number}: {other_route.method} {other_route.path} (specificity: {other_route.specificity_score})\n"
                        f"  Solution: Move the more specific route before the generic one"
                    )
    
    return issues


def would_conflict(route1: RouteInfo, route2: RouteInfo) -> bool:
    """Check if two routes would conflict (first route catches second route's requests)"""
    if route1.method != route2.method:
        return False
    
    # If first route is more generic and comes before more specific route
    if route1.specificity_score < route2.specificity_score:
        return paths_would_match(route1.path, route2.path)
    
    return False


def paths_would_match(generic_path: str, specific_path: str) -> bool:
    """Check if a generic path pattern would match a specific path"""
    # Simple check: if generic path has parameters that could match specific path segments
    generic_segments = generic_path.strip("/").split("/")
    specific_segments = specific_path.strip("/").split("/")
    
    if len(generic_segments) != len(specific_segments):
        return False
    
    for gen_seg, spec_seg in zip(generic_segments, specific_segments):
        if "{" in gen_seg and "}" in gen_seg:
            # Parameter segment can match anything
            continue
        elif gen_seg != spec_seg:
            # Static segments must match exactly
            return False
    
    return True


def main():
    """Main validation function"""
    # Find all router files in the API endpoints directory
    api_dir = Path("app/api/endpoints")
    
    if not api_dir.exists():
        print(f"Error: {api_dir} not found. Run this script from campaign_crafter_api directory.")
        sys.exit(1)
    
    router_files = list(api_dir.glob("*.py"))
    router_files = [f for f in router_files if f.name != "__init__.py"]
    
    all_issues = []
    
    for router_file in sorted(router_files):
        print(f"\n=== Validating {router_file} ===")
        routes = extract_routes_from_file(router_file)
        
        if not routes:
            print("  No routes found")
            continue
        
        print(f"Found {len(routes)} routes:")
        for route in routes:
            print(f"  {route}")
        
        issues = validate_route_order(routes)
        if issues:
            print(f"\n❌ Found {len(issues)} route ordering issues:")
            for issue in issues:
                print(f"\n{issue}")
            all_issues.extend(issues)
        else:
            print("✅ No route ordering issues found")
    
    if all_issues:
        print(f"\n{'='*80}")
        print(f"❌ TOTAL ISSUES FOUND: {len(all_issues)}")
        print(f"{'='*80}")
        print("\nTo fix these issues:")
        print("1. Move specific routes (without parameters) before generic routes (with parameters)")
        print("2. Move routes with more path segments before routes with fewer segments")
        print("3. For routes with same path structure, use different paths (e.g., /features/by-name/{name})")
        print("4. Add comments like '# Must come before /{id}' to document ordering requirements")
        sys.exit(1)
    else:
        print(f"\n{'='*80}")
        print("✅ All route orders are correct!")
        print(f"{'='*80}")
        sys.exit(0)


if __name__ == "__main__":
    main()
