#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from datetime import datetime

# Create root element
root = ET.Element('urlset')
root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

def add_url(loc, lastmod, changefreq, priority):
    """Add URL element to sitemap"""
    url = ET.SubElement(root, 'url')
    
    loc_el = ET.SubElement(url, 'loc')
    loc_el.text = loc
    
    lastmod_el = ET.SubElement(url, 'lastmod')
    lastmod_el.text = lastmod
    
    changefreq_el = ET.SubElement(url, 'changefreq')
    changefreq_el.text = changefreq
    
    priority_el = ET.SubElement(url, 'priority')
    priority_el.text = priority

# Core pages
add_url('https://lakefrontleakanddrain.com/', '2026-04-02', 'weekly', '1.0')
add_url('https://lakefrontleakanddrain.com/services/', '2026-03-05', 'weekly', '0.9')
add_url('https://lakefrontleakanddrain.com/areas/', '2026-03-05', 'monthly', '0.8')
add_url('https://lakefrontleakanddrain.com/blog/', '2026-03-05', 'weekly', '0.8')
add_url('https://lakefrontleakanddrain.com/contact/', '2026-03-05', 'monthly', '0.8')
add_url('https://lakefrontleakanddrain.com/reviews/', '2026-03-05', 'weekly', '0.8')
add_url('https://lakefrontleakanddrain.com/referrals/', '2026-03-05', 'monthly', '0.7')

# Service pages
services = [
    ('emergency-plumber-cleveland/', '2026-03-05'),
    ('plumbing-repair-cleveland/', '2026-03-06'),
    ('drain-cleaning-cleveland/', '2026-03-05'),
    ('clogged-drain-cleveland/', '2026-03-06'),
    ('leak-repair-cleveland/', '2026-03-05'),
    ('leaking-pipe-repair-cleveland/', '2026-03-06'),
    ('pipe-repair-cleveland/', '2026-03-05'),
    ('water-pressure-problems-cleveland/', '2026-03-06'),
    ('water-pressure-diagnosis-cleveland/', '2026-03-05'),
    ('sewer-smell-basement-cleveland/', '2026-03-06'),
    ('basement-flooding-cleveland/', '2026-03-05'),
    ('sump-pump-installation-cleveland/', '2026-03-05'),
    ('sump-pump-repair-cleveland/', '2026-03-05'),
    ('sump-pump-inspection-cleveland/', '2026-03-06'),
    ('main-line-drain-clearing-cleveland/', '2026-03-05'),
    ('frozen-pipe-repair-cleveland/', '2026-03-05'),
    ('faucet-repair-cleveland/', '2026-03-05'),
    ('faucet-installation-cleveland/', '2026-03-05'),
    ('toilet-repair-cleveland/', '2026-03-05'),
    ('toilet-installation-cleveland/', '2026-03-05'),
    ('water-heater-repair-cleveland/', '2026-03-05'),
    ('water-heater-replacement-cleveland/', '2026-03-05'),
    ('tankless-water-heater-cleveland/', '2026-03-05'),
    ('water-filtration-installation-cleveland/', '2026-03-05'),
    ('garbage-disposal-installation-cleveland/', '2026-03-05'),
    ('garbage-disposal-repair-cleveland/', '2026-03-05'),
    ('dishwasher-installation-cleveland/', '2026-03-05'),
    ('laundry-plumbing-cleveland/', '2026-03-05'),
    ('kitchen-plumbing-repair-cleveland/', '2026-03-05'),
    ('bathroom-plumbing-repair-cleveland/', '2026-03-05'),
    ('appliance-installation-cleveland/', '2026-03-05'),
    ('backflow-service-cleveland/', '2026-03-05'),
    ('gas-leak-check-cleveland/', '2026-03-05'),
    ('hose-bib-repair-cleveland/', '2026-03-05'),
    ('shutoff-valve-replacement-cleveland/', '2026-03-05'),
    ('plumbing-inspection-cleveland/', '2026-03-05'),
]

for service, lastmod in services:
    add_url(f'https://lakefrontleakanddrain.com/{service}', lastmod, 'weekly', '0.8')

# Location pages
cities = [
    'amherst', 'aurora', 'avon-lake', 'avon', 'bainbridge', 'bay-village',
    'beachwood', 'bedford-heights', 'bedford', 'bentleyville', 'berea', 'brecksville',
    'broadview-heights', 'brook-park', 'brooklyn-centre', 'brooklyn-heights', 'brooklyn',
    'brunswick-hills', 'brunswick', 'buckeye-shaker', 'chagrin-falls', 'chagrin-falls-township',
    'clark-fulton', 'cleveland-heights', 'cleveland', 'collinwood', 'concord', 'concord-township',
    'cudell', 'cuyahoga-heights', 'detroit-shoreway', 'downtown-cleveland', 'east-cleveland',
    'eastlake', 'edgewater', 'elyria', 'euclid', 'fairfax', 'fairport-harbor', 'fairview-park',
    'garfield-heights', 'gates-mills', 'glenville', 'glenwillow', 'goodrich-kirtland-park',
    'gordon-square', 'grand-river', 'highland-heights', 'highland-hills', 'hinckley', 'hough',
    'hudson', 'hunting-valley', 'independence', 'jefferson', 'kamm-s-corners', 'kinsman',
    'kirtland-hills', 'kirtland', 'lakeline', 'lakewood', 'lee-harvard', 'linndale',
    'litchfield', 'little-italy', 'lorain', 'lyndhurst', 'macedonia', 'madison',
    'madison-township', 'maple-heights', 'mayfield-heights', 'mayfield-village', 'medina',
    'medina-township', 'mentor', 'mentor-on-the-lake', 'middleburg-heights', 'moreland-hills',
    'mount-pleasant', 'newburgh-heights', 'north-olmsted', 'north-ridgeville', 'north-royalton',
    'northfield', 'oakwood-village', 'oberlin', 'ohio-city', 'old-brooklyn', 'olmsted-falls',
    'olmsted-township', 'orange', 'painesville', 'parma-heights', 'parma', 'parma-township',
    'pepper-pike', 'richmond-heights', 'rocky-river', 'sagamore-hills', 'seven-hills',
    'seville', 'shaker-heights', 'sheffield-lake', 'sheffield-village', 'shoreway',
    'slavic-village', 'solon', 'south-euclid', 'st-clair-superior', 'stockyards',
    'strongsville', 'tremont', 'twinsburg', 'university-circle', 'university-heights',
    'valley-view', 'vermilion', 'wadsworth', 'waite-hill', 'walton-hills',
    'warrensville-heights', 'west-park', 'westlake', 'wickliffe', 'willoughby',
    'willowick', 'woodmere'
]

major_cities = {'cleveland', 'cleveland-heights', 'downtown-cleveland', 'lakewood'}

for city in cities:
    priority = '0.7' if city in major_cities else '0.6'
    add_url(f'https://lakefrontleakanddrain.com/plumber-{city}-oh/', '2026-03-05', 'monthly', priority)

# Write to file
tree = ET.ElementTree(root)
ET.indent(tree, space='  ')
tree.write('sitemap.xml', encoding='UTF-8', xml_declaration=True)
print(f'Sitemap generated with {len(root)} entries')
