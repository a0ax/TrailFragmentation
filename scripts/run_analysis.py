#!/usr/bin/env python
import sys
import os
import glob
import geopandas as gpd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

from fragmentation import TrailFragmentationAnalyzer
from visualize import TrailVisualizer

def filter_protected_areas(gdf):
    """Filter swissTLMRegio Landcover to only include protected areas."""
    print("🔍 Filtering for protected areas...")
    print(f"   Total features: {len(gdf)}")
    
    # Show OBJORIG distribution
    print("\n📊 OBJORIG value counts:")
    print(gdf['OBJORIG'].value_counts())
    
    # Protected area codes: NMA_* (National/International protected areas) and ERM (Mires)
    mask = (
        gdf['OBJORIG'].str.startswith('NMA_', na=False) |
        gdf['OBJORIG'].isin(['ERM'])
    )
    
    filtered = gdf[mask]
    
    print(f"\n✅ Found {len(filtered)} protected area features:")
    if len(filtered) > 0:
        print(filtered['OBJORIG'].value_counts())
        area_km2 = filtered.geometry.area.sum() / 1e6
        print(f"   Total protected area: {area_km2:.2f} km²")
        
        # Show some names
        if 'NAMN1' in filtered.columns:
            names = filtered[filtered['NAMN1'] != 'N_A']['NAMN1'].dropna().unique()
            if len(names) > 0:
                print(f"\n📋 Protected area names (sample):")
                for name in names[:10]:
                    print(f"   - {name}")
    else:
        print("⚠️ No protected areas found. Check the column names.")
        print("   Available columns:", gdf.columns.tolist())
        print("   OBJORIG values:", gdf['OBJORIG'].unique()[:20])
    
    return filtered

def main():
    # --- CONFIGURATION ---
    landcover_shp = 'data/boundaries/swissTLMRegio_LandCover.shp'
    
    if not os.path.exists(landcover_shp):
        print(f"❌ Landcover shapefile not found at: {landcover_shp}")
        print("   Make sure you extracted the swissTLMRegio dataset correctly.")
        return
    
    print(f"📁 Loading landcover data from: {landcover_shp}")
    landcover = gpd.read_file(landcover_shp)
    print(f"   Total landcover features: {len(landcover)}")
    
    # Filter to only protected areas
    protected_area = filter_protected_areas(landcover)
    print(f"\n   Protected area features: {len(protected_area)}")
    
    if len(protected_area) == 0:
        print("❌ No protected areas found. Exiting.")
        return
    
    # Save filtered protected areas for faster loading next time
    filtered_path = 'data/boundaries/protected_areas_filtered.shp'
    protected_area.to_file(filtered_path)
    print(f"   Saved filtered protected areas to {filtered_path}")
    
    # Find GPX files
    gpx_files = glob.glob('data/raw/*.gpx')
    if not gpx_files:
        print("❌ No GPX files found in data/raw/")
        print("   Place your GPX files in data/raw/")
        return
    
    print(f"   GPX files found: {len(gpx_files)}")
    
    # Initialize analyzer with filtered protected areas
    analyzer = TrailFragmentationAnalyzer(filtered_path, buffer_distance=10)
    
    # Run analysis
    results = analyzer.run_full_analysis(gpx_files)
    analyzer.export_results(results, 'outputs/tables')
    
    # Load trails for visualization
    trails = analyzer.load_trails(gpx_files)
    
    # Create visualizations
    viz = TrailVisualizer()
    os.makedirs('outputs/figures', exist_ok=True)
    
    viz.create_fragmentation_map(analyzer.protected_area, trails, 
                                 'outputs/figures/fragmentation_map.png',
                                 buffer_distance=10)
    viz.create_metrics_dashboard(results, 'outputs/figures/metrics_dashboard.png')
    viz.create_interactive_map(analyzer.protected_area, trails,
                               'outputs/figures/interactive_map.html')
    
    print("\n✅ Analysis complete! Check the outputs/ directory.")
    print("\n📋 KEY FINDINGS:")
    frag = results['fragmentation']
    print(f"   Fragmentation Index: {frag['fragmentation_percent']:.2f}%")
    print(f"   Affected Area: {frag['affected_area_km2']:.2f} km²")
    print(f"   Trail Density: {frag['trail_density_km_per_km2']:.2f} km/km²")
    print(f"   Core Habitat Remaining: {frag['core_habitat_percent']:.1f}%")

if __name__ == "__main__":
    main()