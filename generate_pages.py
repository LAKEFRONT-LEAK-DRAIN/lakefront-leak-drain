from pathlib import Path
import re
from datetime import date

# Write generated files into this repository root by default.
root = Path(__file__).resolve().parent
book_url = 'https://book.housecallpro.com/book/Lakefront-Leak--Drain/ae2653195f4d42308810145d8ff8bf21?v2=true'
portal_url = 'https://client.housecallpro.com/customer_portal/request-link?token=19d1b66af5ca4e928d038e6f3caa0f44'
review_url = 'https://g.page/r/CclR-stJDa4UEBI/review'
google_url = 'https://maps.app.goo.gl/LuGPYCWh3e2hYKaB6?g_st=ic'
phone = '216-505-7765'
email = 'Lakefrontleakanddrain@gmail.com'
img = '/img/cities/plumber-cleveland-oh.jpg'
lastmod = '2026-03-06'

pages = {
    'leak-repair-cleveland': {
        'title': 'Leak Repair in Cleveland | Lakefront Leak & Drain',
        'meta': 'Professional leak repair in Cleveland for pipe leaks, fixture leaks, shutoff leaks, and hidden moisture problems. Call or book online.',
        'h1': 'Leak Repair in Cleveland',
        'kicker': 'Fast residential leak & drain help',
        'hero': 'Professional help for leaking pipes, fixture leaks, shutoff issues, and hidden plumbing moisture.',
        'badge1': 'Leak diagnosis', 'badge2': 'Clean repairs', 'badge3': 'Text updates',
        'image_alt': 'Leak repair service in Cleveland',
        'intro_h2': 'Professional leak repair for Cleveland homes',
        'intro_p': 'Water leaks can damage cabinets, drywall, floors, and finished basements if they are left alone. Lakefront Leak & Drain provides leak repair in Cleveland for common residential plumbing problems including dripping supply lines, leaking shutoff valves, under-sink leaks, fixture leaks, and visible pipe leaks. We focus on clear options, clean work, and straightforward communication.',
        'reasons': ['Water under sinks or around fixtures', 'Stains on ceilings, walls, or flooring', 'Musty odors or damp spots', 'Dripping shutoff valves or supply lines'],
        'expect': ['Clear explanation before work begins', 'Careful diagnosis of visible leak source', 'Tidy work area and clean finish'],
        'services_h2': 'What leak repair service may include',
        'services_p': 'Service may include isolating the source of a visible leak, repairing or replacing damaged fittings, supply lines, shutoff valves, traps, or short sections of pipe, and checking the immediate repair area for proper operation. If hidden conditions or additional damage are discovered, updated options can be provided before additional work begins.',
        'signs_h2': 'Common signs you may need leak repair',
        'signs': ['Unexpected water on floors or inside cabinets', 'Water stains, bubbling paint, or soft drywall', 'Higher water bills without a clear reason', 'Sounds of running water when fixtures are off', 'Visible corrosion, drips, or moisture around plumbing connections'],
        'faq': [
            ('Do you repair under-sink leaks?', 'Yes. We commonly diagnose and repair leaks at supply lines, traps, drain connections, shutoff valves, and fixture connections.'),
            ('Can a small leak turn into a bigger problem?', 'Yes. Even a slow leak can damage cabinets, flooring, drywall, and nearby finishes over time.'),
            ('Do you serve areas outside Cleveland?', 'Yes. Lakefront Leak & Drain serves Cleveland, Lakewood, and nearby Cuyahoga County communities.')
        ]
    },
    'drain-cleaning-cleveland': {
        'title': 'Drain Cleaning in Cleveland | Lakefront Leak & Drain',
        'meta': 'Drain cleaning in Cleveland for slow drains, recurring clogs, backups, and drain odors. Residential service across Cleveland and nearby areas.',
        'h1': 'Drain Cleaning in Cleveland',
        'kicker': 'Fast residential leak & drain help',
        'hero': 'Clear slow drains, recurring clogs, backups, and drain odor issues with professional residential service.',
        'badge1': 'Slow drains', 'badge2': 'Recurring clogs', 'badge3': 'Clean work area',
        'image_alt': 'Drain cleaning service in Cleveland',
        'intro_h2': 'Professional drain cleaning for residential plumbing',
        'intro_p': 'Slow or blocked drains can disrupt kitchens, bathrooms, laundry areas, and basement plumbing. Lakefront Leak & Drain provides drain cleaning in Cleveland for common residential drain issues including sluggish sinks, tub and shower drain buildup, and recurring clogs. The goal is to restore flow, explain what was found, and recommend the next step if a deeper issue is suspected.',
        'reasons': ['Kitchen sinks draining slowly', 'Tub and shower backups', 'Recurring sink clogs', 'Drain odors or gurgling sounds'],
        'expect': ['Clear explanation and upfront options', 'Service focused on restoring flow', 'Recommendations if recurring problems point to a deeper issue'],
        'services_h2': 'What drain cleaning service may include',
        'services_p': 'Service may include clearing accessible clogs, removing common buildup such as hair, soap residue, grease, and debris, and testing the fixture after service. If symptoms suggest a larger drain or sewer issue, additional diagnostic recommendations such as camera inspection may be provided.',
        'signs_h2': 'Common signs you may need drain cleaning',
        'signs': ['Water draining slowly from sinks, tubs, or showers', 'Frequent clogs in the same fixture', 'Water backing up into nearby fixtures', 'Gurgling sounds after using plumbing fixtures', 'Persistent drain odors'],
        'faq': [
            ('Does drain cleaning guarantee the problem will never come back?', 'Not always. If underlying issues such as roots, pipe offsets, scale buildup, or improper pitch exist, stoppages can recur.'),
            ('Do you handle drain problems in basements?', 'Yes. We can evaluate common residential drain issues affecting basement plumbing and nearby fixtures.'),
            ('Do you serve Lakewood and nearby suburbs?', 'Yes. Lakefront Leak & Drain serves Cleveland, Lakewood, and nearby communities.')
        ]
    },
    'sump-pump-repair-cleveland': {
        'title': 'Sump Pump Repair in Cleveland | Lakefront Leak & Drain',
        'meta': 'Sump pump repair in Cleveland for pumps that will not run, run constantly, make noise, or fail during rain. Residential plumbing service.',
        'h1': 'Sump Pump Repair in Cleveland',
        'kicker': 'Basement flood prevention support',
        'hero': 'Help for sump pumps that will not start, run nonstop, cycle incorrectly, or show signs of wear before heavy rain.',
        'badge1': 'Storm prep', 'badge2': 'Pump troubleshooting', 'badge3': 'Cleveland homes',
        'image_alt': 'Sump pump repair service in Cleveland',
        'intro_h2': 'Sump pump repair for Cleveland basements',
        'intro_p': 'Cleveland basements deal with spring rain, snowmelt, and groundwater pressure that can put a sump system to work quickly. Lakefront Leak & Drain provides sump pump repair in Cleveland for residential systems that are noisy, unreliable, cycling too often, or failing to remove water properly. The focus is on diagnosing what the pump is doing, checking key components, and recommending the best next step.',
        'reasons': ['Pump does not activate during rain', 'Pump runs constantly or short cycles', 'Unusual noises from the pit area', 'Water staying in the sump pit'],
        'expect': ['Clear explanation of observed sump pump condition', 'Testing of common operating issues', 'Recommendations based on basement flood risk and system age'],
        'services_h2': 'What sump pump repair service may include',
        'services_p': 'Service may include inspection of the sump pit area, basic operational testing, checking the float and discharge behavior, and diagnosing common failure symptoms. If replacement is the better option due to age or condition, updated recommendations can be provided before work proceeds.',
        'signs_h2': 'Common signs you may need sump pump repair',
        'signs': ['Pump does not turn on when water rises', 'Pump runs but water does not leave the pit effectively', 'Loud vibration, rattling, or humming', 'Frequent cycling during wet weather', 'Visible rust, wear, or aging at the system'],
        'faq': [
            ('Should a sump pump be checked before spring rain?', 'Yes. Testing before wet weather can help identify issues before the system is under heavy demand.'),
            ('Can you help if my basement has had water before?', 'Yes. We can evaluate common sump and drainage-related plumbing concerns that contribute to basement water issues.'),
            ('Do you serve more than Cleveland?', 'Yes. Service is available across Cleveland, Lakewood, and nearby Cuyahoga County communities.')
        ]
    },
    'basement-flooding-cleveland': {
        'title': 'Basement Flooding Help in Cleveland | Lakefront Leak & Drain',
        'meta': 'Basement flooding help in Cleveland for sump pump issues, drain backups, and storm-related plumbing concerns. Residential service across Cleveland.',
        'h1': 'Basement Flooding Help in Cleveland',
        'kicker': 'Storm season plumbing support',
        'hero': 'Professional help for basement water issues, sump pump concerns, and plumbing conditions that can contribute to flooding.',
        'badge1': 'Sump pump checks', 'badge2': 'Drain concerns', 'badge3': 'Storm prep',
        'image_alt': 'Basement flooding help in Cleveland',
        'intro_h2': 'Help reduce basement water risk',
        'intro_p': 'Basement water problems can come from more than one source. Sump pump failure, blocked drains, heavy rain, and hidden plumbing issues can all contribute to water showing up where it should not. Lakefront Leak & Drain provides basement flooding help in Cleveland by evaluating common residential plumbing factors that affect basement water problems and recommending practical next steps.',
        'reasons': ['Water collecting near the sump pit', 'Floor drains backing up during storms', 'Basement moisture concerns', 'Past flooding during heavy rain'],
        'expect': ['Straightforward explanation of likely plumbing contributors', 'Recommendations based on what is visible and testable', 'Local service focused on Cleveland homes and basements'],
        'services_h2': 'Common plumbing issues linked to basement flooding',
        'services_p': 'Common contributors include sump pump failure, discharge issues, blocked drains, recurring clogs, and aging plumbing components that do not perform well under storm conditions. Service may include inspection, testing, and recommendations for repair or replacement where needed.',
        'signs_h2': 'When to schedule basement flooding help',
        'signs': ['Water entering the basement during storms', 'A sump pump that does not seem to keep up', 'Slow floor drains or drain backups', 'Signs of moisture, mildew, or repeated dampness', 'Past flooding that you do not want repeated'],
        'faq': [
            ('Can you inspect my sump pump if I am worried about flooding?', 'Yes. Sump pump inspection and troubleshooting are common parts of basement flood prevention service.'),
            ('Do you handle recurring basement drain issues?', 'Yes. We can evaluate common residential drain symptoms and recommend the next step if a larger issue is suspected.'),
            ('Do you serve nearby suburbs too?', 'Yes. Lakefront Leak & Drain serves Cleveland, Lakewood, and nearby communities.')
        ]
    },
    'clogged-drain-cleveland': {
        'title': 'Clogged Drain Repair in Cleveland | Lakefront Leak & Drain',
        'meta': 'Clogged drain repair in Cleveland for blocked sinks, tubs, showers, and recurring residential drain backups. Fast local service.',
        'h1': 'Clogged Drain Repair in Cleveland',
        'kicker': 'Fast residential leak & drain help',
        'hero': 'Help for blocked drains, backups, and recurring clogs in kitchens, bathrooms, basements, and laundry areas.',
        'badge1': 'Blocked drains', 'badge2': 'Recurring backups', 'badge3': 'Local Cleveland service',
        'image_alt': 'Clogged drain repair in Cleveland',
        'intro_h2': 'Professional help for clogged residential drains',
        'intro_p': 'A clogged drain can interrupt daily routines quickly, especially when a kitchen sink, shower, or basement drain starts backing up. Lakefront Leak & Drain provides clogged drain repair in Cleveland for common residential drain problems. Service focuses on restoring usable flow, checking for obvious recurring issues, and explaining the next step if the blockage appears to be part of a larger problem.',
        'reasons': ['Standing water in sinks or tubs', 'Slow draining fixtures', 'Repeated drain backups', 'Gurgling or foul drain odor'],
        'expect': ['Upfront communication before work begins', 'Service focused on the affected fixture or line', 'Recommendations if deeper drain issues are suspected'],
        'services_h2': 'What causes clogged drains',
        'services_p': 'Common causes include grease buildup, soap residue, hair, food particles, wipes, and foreign objects in the line. Older homes may also have scale buildup or other pipe conditions that contribute to recurring stoppages. Service is tailored to what is visible, accessible, and appropriate for the drain condition.',
        'signs_h2': 'Common signs of a clogged drain',
        'signs': ['Water draining slowly or not at all', 'Water backing up into tubs or nearby fixtures', 'Repeated clogs in the same drain', 'Unpleasant odors from the drain opening', 'Bubbling or gurgling after using nearby plumbing fixtures'],
        'faq': [
            ('Do you handle recurring clogged drain issues?', 'Yes. Recurring clogs are common, and if the pattern suggests a deeper issue, additional diagnostic recommendations can be provided.'),
            ('Can a clogged drain affect more than one fixture?', 'Yes. When multiple fixtures are involved, the blockage may be deeper in the system than a single sink or tub drain.'),
            ('Do you serve Cleveland and Lakewood?', 'Yes. Service is available across Cleveland, Lakewood, and nearby communities.')
        ]
    },
    'plumbing-repair-cleveland': {
        'title': 'Plumbing Repair in Cleveland | Lakefront Leak & Drain',
        'meta': 'Residential plumbing repair in Cleveland for leaks, drain problems, shutoff issues, fixture repairs, and common home plumbing concerns.',
        'h1': 'Residential Plumbing Repair in Cleveland',
        'kicker': 'Fast residential leak & drain help',
        'hero': 'General plumbing repair for common residential problems including leaks, drain issues, fixture concerns, and aging plumbing components.',
        'badge1': 'Residential repairs', 'badge2': 'Clear options', 'badge3': 'Book online',
        'image_alt': 'Plumbing repair service in Cleveland',
        'intro_h2': 'Professional plumbing repair for everyday home issues',
        'intro_p': 'Home plumbing systems wear down over time. Small leaks, weak shutoff valves, drain problems, and fixture issues can all turn into larger disruptions if they are ignored. Lakefront Leak & Drain provides plumbing repair in Cleveland for a wide range of common residential plumbing problems with a focus on straightforward communication, clean work, and practical options.',
        'reasons': ['Visible plumbing leaks', 'Drain and fixture performance issues', 'Aging shutoff valves or supply lines', 'General residential plumbing concerns'],
        'expect': ['Clear explanation of the issue and next steps', 'Residential service tailored to the problem observed', 'Recommendations if hidden conditions are found'],
        'services_h2': 'Common plumbing repair services',
        'services_p': 'Common repair work may include leak repairs, shutoff valve replacement, drain issue diagnosis, fixture connection repairs, under-sink plumbing repairs, and troubleshooting for low pressure or water-related plumbing concerns. Service recommendations are based on the visible scope and condition of the plumbing system.',
        'signs_h2': 'When to schedule plumbing repair',
        'signs': ['Leaks, drips, or visible water damage', 'Recurring drain or fixture problems', 'Loss of water pressure at one or more fixtures', 'Strange noises, odors, or repeated plumbing issues', 'Old plumbing components that no longer operate reliably'],
        'faq': [
            ('Do you handle general plumbing repairs for homeowners?', 'Yes. Lakefront Leak & Drain focuses on residential plumbing repairs across Cleveland and nearby communities.'),
            ('Can you explain options before work begins?', 'Yes. Clear communication and upfront options are part of the service experience.'),
            ('Do you serve nearby suburbs too?', 'Yes. Service is available across Cleveland, Lakewood, and surrounding areas.')
        ]
    },
    'sump-pump-inspection-cleveland': {
        'title': 'Sump Pump Inspection in Cleveland | Lakefront Leak & Drain',
        'meta': 'Sump pump inspection in Cleveland to test operation, check warning signs, and help prepare basements for spring rain and storm season.',
        'h1': 'Sump Pump Inspection in Cleveland',
        'kicker': 'Basement flood prevention support',
        'hero': 'Professional sump pump inspection and testing for Cleveland homeowners preparing for spring rain, storms, and basement water risk.',
        'badge1': 'Spring prep', 'badge2': 'Pump testing', 'badge3': 'Basement protection',
        'image_alt': 'Sump pump inspection in Cleveland',
        'intro_h2': 'Sump pump inspections before heavy rain matter',
        'intro_p': 'A sump pump often gets ignored until the weather turns wet and the basement starts taking on water. Lakefront Leak & Drain provides sump pump inspection in Cleveland to help homeowners understand how their current system is performing before storm season puts it to the test. This service is useful before spring rain, during snowmelt, or anytime the system has not been checked recently.',
        'reasons': ['Spring rain is approaching', 'The pump has not been tested recently', 'The basement has flooded before', 'The system is older or showing signs of wear'],
        'expect': ['Operational testing of visible sump pump performance', 'Discussion of warning signs and maintenance needs', 'Recommendations if repair or replacement is the better next step'],
        'services_h2': 'What a sump pump inspection may include',
        'services_p': 'Inspection may include checking visible operation, observing how the pump activates, looking for warning signs such as noise, rust, or short cycling, and reviewing obvious discharge concerns. If problems are found, repair or replacement options can be provided before work proceeds.',
        'signs_h2': 'When a sump pump inspection is a good idea',
        'signs': ['Before spring storms or heavy rain periods', 'After previous basement flooding', 'When the pump seems noisy or unreliable', 'If the system is older and has not been checked recently', 'If the pit holds water longer than expected'],
        'faq': [
            ('Should I have my sump pump checked before April showers?', 'Yes. A pre-season inspection can help identify issues before heavy rain arrives.'),
            ('Can an inspection tell me if I need repair or replacement?', 'It can often identify visible warning signs and operating problems that help guide the next recommendation.'),
            ('Do you provide sump pump service outside Cleveland?', 'Yes. Lakefront Leak & Drain serves Cleveland, Lakewood, and nearby communities.')
        ]
    },
    'water-pressure-problems-cleveland': {
        'title': 'Water Pressure Problems in Cleveland | Lakefront Leak & Drain',
        'meta': 'Help with water pressure problems in Cleveland, including low pressure, uneven fixture pressure, and common residential plumbing causes.',
        'h1': 'Water Pressure Problems in Cleveland',
        'kicker': 'Residential plumbing diagnosis',
        'hero': 'Help diagnosing low water pressure, uneven pressure at fixtures, and other common residential water pressure concerns.',
        'badge1': 'Low pressure', 'badge2': 'Fixture diagnosis', 'badge3': 'Clear recommendations',
        'image_alt': 'Water pressure problems in Cleveland',
        'intro_h2': 'Diagnosing water pressure issues at home',
        'intro_p': 'Low or inconsistent water pressure can make everyday plumbing frustrating and may point to hidden plumbing issues, failing components, or localized restrictions in the system. Lakefront Leak & Drain provides help with water pressure problems in Cleveland by diagnosing visible symptoms and recommending practical next steps for homeowners.',
        'reasons': ['Weak flow at sinks or showers', 'Pressure drops when multiple fixtures run', 'One fixture has poor pressure while others do not', 'Pressure issues after plumbing changes or repairs'],
        'expect': ['Evaluation of visible fixture and plumbing symptoms', 'Clear explanation of likely causes', 'Recommendations based on the system and scope observed'],
        'services_h2': 'Common causes of water pressure problems',
        'services_p': 'Common causes can include clogged aerators, failing fixture parts, partially closed shutoff valves, localized buildup, aging plumbing, or pressure-related supply concerns. Diagnosis helps narrow down whether the issue appears isolated to a fixture, a branch line, or a broader plumbing condition.',
        'signs_h2': 'Common water pressure complaints',
        'signs': ['Weak shower or sink flow', 'Pressure that changes during use', 'Poor hot water pressure only', 'One area of the home with lower pressure than the rest', 'Visible aging or corroded plumbing components'],
        'faq': [
            ('Can low pressure be caused by an old shutoff valve or supply line?', 'Yes. Aging components can restrict flow and contribute to pressure complaints.'),
            ('Do you diagnose pressure problems at one fixture or throughout the home?', 'Yes. Diagnosis can help determine whether the issue appears localized or more widespread.'),
            ('Do you already offer water pressure diagnosis?', 'Yes. Lakefront Leak & Drain provides residential water pressure diagnosis in Cleveland and nearby communities.')
        ]
    },
    'sewer-smell-basement-cleveland': {
        'title': 'Sewer Smell in Basement in Cleveland | Lakefront Leak & Drain',
        'meta': 'Help with sewer smell in basement in Cleveland. Diagnose common residential drain and plumbing causes of basement sewer odor.',
        'h1': 'Sewer Smell in Basement in Cleveland',
        'kicker': 'Basement drain and odor concerns',
        'hero': 'Help diagnosing sewer odor in basements, drain smell issues, and common residential plumbing causes of persistent basement odor.',
        'badge1': 'Basement odors', 'badge2': 'Drain concerns', 'badge3': 'Local diagnosis',
        'image_alt': 'Sewer smell in basement in Cleveland',
        'intro_h2': 'Professional help for basement sewer odor',
        'intro_p': 'A sewer smell in the basement can be frustrating and may point to a drain problem, standing water issue, trap concern, or another plumbing-related condition. Lakefront Leak & Drain provides help with sewer smell in basement areas in Cleveland by evaluating visible symptoms and common residential plumbing causes. The goal is to identify likely sources and explain practical next steps.',
        'reasons': ['Persistent sewer odor near basement drains', 'Smell that gets worse after rain or drain use', 'Musty or unpleasant odor near plumbing fixtures', 'Recurring basement drain concerns'],
        'expect': ['Review of likely plumbing-related odor sources', 'Straightforward explanation of visible findings', 'Recommendations based on basement plumbing conditions'],
        'services_h2': 'Common causes of sewer smell in a basement',
        'services_p': 'Common causes may include drain trap problems, infrequently used drains, drain or vent issues, standing water conditions, and deeper sewer or line concerns. Because basement odor can have more than one source, diagnosis starts with what is visible, accessible, and most likely based on the symptoms described.',
        'signs_h2': 'When to schedule a sewer smell evaluation',
        'signs': ['Odor coming from a floor drain or nearby plumbing fixture', 'Basement smell after storms or heavy drain use', 'Recurring odor that comes and goes', 'Basement drain issues combined with backups or slow flow', 'A smell strong enough to affect finished basement areas'],
        'faq': [
            ('Can a dry floor drain cause sewer smell?', 'Yes. In some cases, an unused drain or other trap issue can contribute to odor concerns.'),
            ('Does sewer odor always mean a sewer backup?', 'No. Odor can come from several plumbing-related causes, which is why diagnosis matters.'),
            ('Do you serve nearby suburbs as well?', 'Yes. Lakefront Leak & Drain serves Cleveland, Lakewood, and nearby communities.')
        ]
    },
    'leaking-pipe-repair-cleveland': {
        'title': 'Leaking Pipe Repair in Cleveland | Lakefront Leak & Drain',
        'meta': 'Leaking pipe repair in Cleveland for visible pipe leaks, dripping pipe joints, basement pipe leaks, and common residential plumbing issues.',
        'h1': 'Leaking Pipe Repair in Cleveland',
        'kicker': 'Fast residential leak & drain help',
        'hero': 'Professional help for leaking pipes, dripping joints, basement pipe leaks, and common residential pipe repair needs.',
        'badge1': 'Pipe leaks', 'badge2': 'Basement repairs', 'badge3': 'Residential service',
        'image_alt': 'Leaking pipe repair in Cleveland',
        'intro_h2': 'Pipe leak repair for visible residential plumbing leaks',
        'intro_p': 'A leaking pipe can start as a slow drip and quickly turn into damage around walls, ceilings, basements, and finished spaces. Lakefront Leak & Drain provides leaking pipe repair in Cleveland for visible residential pipe leaks including exposed basement lines, under-sink pipe leaks, dripping joints, and common household plumbing leak points. Service focuses on stopping the active leak and explaining any related conditions that should be addressed.',
        'reasons': ['Dripping exposed pipes in basements or utility areas', 'Leaks at joints, fittings, or nearby shutoffs', 'Moisture under sinks or around exposed plumbing', 'Corroded or aging visible pipe sections'],
        'expect': ['Clear diagnosis of the visible leak area', 'Repair options based on the pipe condition and location', 'Recommendations if surrounding components also show wear'],
        'services_h2': 'What leaking pipe repair may include',
        'services_p': 'Service may include isolating the active leak, repairing or replacing an accessible damaged fitting or pipe section, checking adjacent visible plumbing for obvious wear, and testing the immediate repair area after service. If hidden damage or additional deterioration is discovered, updated recommendations can be provided before further work begins.',
        'signs_h2': 'Common signs of a leaking pipe',
        'signs': ['Visible dripping or moisture on exposed piping', 'Water stains below a known pipe location', 'Rust, corrosion, or mineral buildup at joints', 'Wet areas near basement pipes or utility spaces', 'A persistent drip sound from plumbing lines'],
        'faq': [
            ('Do you repair exposed leaking pipes in basements?', 'Yes. Visible basement pipe leaks and exposed residential plumbing repairs are common service calls.'),
            ('Can an old pipe fail after it starts leaking?', 'Yes. Corrosion or deterioration can worsen quickly once a leak is active.'),
            ('Do you serve Cleveland and nearby communities?', 'Yes. Lakefront Leak & Drain serves Cleveland, Lakewood, and nearby areas.')
        ]
    },
}

related_links = [
    ('/leak-repair-cleveland/', 'Leak Repair'),
    ('/leaking-pipe-repair-cleveland/', 'Leaking Pipe Repair'),
    ('/drain-cleaning-cleveland/', 'Drain Cleaning'),
    ('/clogged-drain-cleveland/', 'Clogged Drain Repair'),
    ('/sump-pump-repair-cleveland/', 'Sump Pump Repair'),
    ('/sump-pump-inspection-cleveland/', 'Sump Pump Inspection'),
    ('/basement-flooding-cleveland/', 'Basement Flooding Help'),
    ('/plumbing-repair-cleveland/', 'Plumbing Repair'),
    ('/water-pressure-problems-cleveland/', 'Water Pressure Problems'),
    ('/water-pressure-diagnosis-cleveland/', 'Water Pressure Diagnosis'),
    ('/sewer-smell-basement-cleveland/', 'Sewer Smell in Basement'),
]

area_links = [
    ('/plumber-cleveland-oh/', 'Cleveland'), ('/plumber-lakewood-oh/', 'Lakewood'), ('/plumber-parma-oh/', 'Parma'), ('/plumber-rocky-river-oh/', 'Rocky River'), ('/plumber-westlake-oh/', 'Westlake'), ('/plumber-brooklyn-oh/', 'Brooklyn'), ('/plumber-cleveland-heights-oh/', 'Cleveland Heights'), ('/areas/', 'View all areas')
]

social_sameas = '["https://www.facebook.com/share/1GeymTYWvK/?mibextid=wwXIfr", "https://www.instagram.com/lakefrontleakanddrain?igsh=NW44MXRmMmFvemRt&utm_source=qr", "https://www.tiktok.com/@lakefront.leak.dr?_r=1&_t=ZP-94RS8xBL85W", "https://youtube.com/@lakefrontleakanddrain?si=UaXb6cs1bHkO2dvk", "https://maps.app.goo.gl/LuGPYCWh3e2hYKaB6?g_st=ic"]'

for slug, d in pages.items():
    url = f'https://lakefrontleakanddrain.com/{slug}/'
    faq_json = ', '.join([f'{{"@type": "Question", "name": "{q}", "acceptedAnswer": {{"@type": "Answer", "text": "{a}"}}}}' for q,a in d['faq']])
    service_links_html = ''.join([f'<a class="button ghost" style="margin:6px 6px 0 0" href="{href}">{text}</a>' for href, text in related_links if href.strip('/') != slug])
    area_links_html = ''.join([f'<a class="button ghost" style="margin:6px 6px 0 0" href="{href}">{text}</a>' for href, text in area_links])
    signs_html = ''.join([f'<li>{x}</li>' for x in d['signs']])
    reasons_html = ''.join([f'<li>{x}</li>' for x in d['reasons']])
    expect_html = ''.join([f'<li>{x}</li>' for x in d['expect']])
    faq_html = ''.join([f'<div class="card" style="margin-top:12px"><h3>{q}</h3><p class="mini">{a}</p></div>' for q,a in d['faq']])
    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{d['title']}</title>
<meta name="description" content="{d['meta']}" />
<link rel="canonical" href="{url}" />
<link rel="stylesheet" href="/styles.css" />
<link rel="icon" href="/logo.jpg" type="image/jpeg" />
<link rel="apple-touch-icon" href="/logo.jpg" />
<meta property="og:title" content="{d['title']}" />
<meta property="og:description" content="{d['meta']}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="https://lakefrontleakanddrain.com/logo.jpg" />
<script type="application/ld+json">[{{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{faq_json}]}}, {{"@context": "https://schema.org", "@type": "Service", "serviceType": "{d['h1']}", "provider": {{"@type": "Plumber", "name": "Lakefront Leak & Drain", "telephone": "+12165057765", "url": "https://lakefrontleakanddrain.com"}}, "areaServed": ["Cleveland, OH", "Lakewood, OH", "Cuyahoga County, OH"]}}, {{"@context": "https://schema.org", "@type": "Plumber", "name": "Lakefront Leak & Drain", "slogan": "Keeping Cleveland Flowing", "url": "https://lakefrontleakanddrain.com", "telephone": "+12165057765", "areaServed": ["Cuyahoga County, OH", "Cleveland, OH"], "sameAs": {social_sameas}, "potentialAction": {{"@type": "ReserveAction", "target": "{book_url}"}}}}]</script>
</head>
<body>
<div class="stickybar">
  <a class="stickybtn" href="tel:+12165057765">Call / Text</a>
  <a class="stickybtn stickybtn--book" href="{book_url}" target="_blank" rel="noopener">Book Online</a>
</div>
<header class="">
  <div class="wrap">
    <div class="topbar">
      <a class="brand" href="/">
        <img src="/logo.jpg" alt="Lakefront Leak & Drain logo" onerror="this.onerror=null;this.src='/logo.png';" />
        <div>
          <b>Lakefront Leak & Drain</b>
          <div class="sub">Keeping Cleveland Flowing • Cleveland &amp; Cuyahoga County</div>
        </div>
      </a>
      <nav><a href="/">Home</a>
<a href="/services/" style="background:rgba(255,255,255,.14)">Services</a>
<a href="/areas/">Service Areas</a>
<a href="/emergency-plumber-cleveland/">Emergency</a>
<a href="/reviews/">Reviews</a>
<a href="/referrals/">Referrals</a>
<a href="/blog/">Tips</a>
<a href="/contact/">Contact</a></nav>
    </div>
    <div class="hero">
      <div class="kicker">{d['kicker']}</div>
      <h1>{d['h1']}</h1>
      <p>{d['hero']}</p>
      <div class="buttons">
        <a class="button call" href="tel:+12165057765">Call / Text: {phone}</a>
        <a class="button book" href="{book_url}" target="_blank" rel="noopener">Book Online</a>
        <a class="button portal" href="{portal_url}" target="_blank" rel="noopener">Customer Portal</a>
      </div>
      <div class="badges">
        <div class="badge">{d['badge1']}</div>
        <div class="badge">{d['badge2']}</div>
        <div class="badge">{d['badge3']}</div>
      </div>
    </div>
  </div>
</header>
<section><div class="wrap"><div class="page-hero"><img src="{img}" alt="{d['image_alt']}" loading="lazy"></div></div></section>
<section><div class="wrap">
<div class="notice" style="border-radius:18px">
  <div class="wrap" style="text-align:center;padding:18px 12px">
    <h2 style="margin:0 0 6px">Need help now?</h2>
    <p style="margin:0 auto;max-width:860px" class="mini">Call/text {phone} or book online in seconds.</p>
    <div class="buttons" style="margin-top:12px">
      <a class="button call" href="tel:+12165057765">Call / Text {phone}</a>
      <a class="button book" href="{book_url}" target="_blank" rel="noopener">Book Online</a>
    </div>
  </div>
</div>
<div class="card" style="margin-top:16px"><h2>{d['intro_h2']}</h2><p class="mini">{d['intro_p']}</p></div>
<div class="grid" style="margin-top:16px">
  <div class="card"><h3>Common reasons people call</h3>
    <ul class="mini">{reasons_html}</ul>
  </div>
  <div class="card"><h3>What you can expect</h3>
    <ul class="mini">{expect_html}</ul>
  </div>
</div>
<div class="card" style="margin-top:16px"><h2>{d['services_h2']}</h2><p class="mini">{d['services_p']}</p></div>
<div class="card" style="margin-top:16px"><h2>{d['signs_h2']}</h2><ul class="mini">{signs_html}</ul></div>
<div class="card" style="margin-top:16px"><h3>Serving Cleveland and nearby communities</h3><p class="mini">Lakefront Leak &amp; Drain provides residential plumbing service across Cleveland, Lakewood, and nearby areas in Cuyahoga County.</p><div style="display:flex;flex-wrap:wrap">{area_links_html}</div></div>
<div class="card" style="margin-top:16px"><h3>Related services</h3><div style="display:flex;flex-wrap:wrap">{service_links_html}</div></div>
</div></section>
<section style="background:var(--bg)"><div class="wrap"><h2 class="section-title" style="text-align:center">Frequently asked questions</h2>{faq_html}</div></section>
<section style="background:var(--bg)">
  <div class="wrap" style="text-align:center">
    <h2 class="section-title">Google Reviews</h2>
    <p class="mini">A quick review helps local homeowners find a reliable pro.</p>
    <div class="buttons" style="margin-top:14px">
      <a class="button book" href="{review_url}" target="_blank" rel="noopener">Leave a Review</a>
      <a class="button call" href="{google_url}" target="_blank" rel="noopener">View on Google</a>
    </div>
  </div>
</section>
<footer>
  <div class="wrap">
    <div><b>Lakefront Leak & Drain</b> — Keeping Cleveland Flowing</div>
    <div style="margin-top:8px">{phone} • <a href="mailto:{email}">{email}</a></div>
    <div class="social">
      <a href="https://www.facebook.com/share/1GeymTYWvK/?mibextid=wwXIfr" target="_blank" rel="noopener">Facebook</a>
      <a href="https://www.instagram.com/lakefrontleakanddrain?igsh=NW44MXRmMmFvemRt&utm_source=qr" target="_blank" rel="noopener">Instagram</a>
      <a href="https://www.tiktok.com/@lakefront.leak.dr?_r=1&_t=ZP-94RS8xBL85W" target="_blank" rel="noopener">TikTok</a>
      <a href="https://youtube.com/@lakefrontleakanddrain?si=UaXb6cs1bHkO2dvk" target="_blank" rel="noopener">YouTube</a>
      <a href="{google_url}" target="_blank" rel="noopener">Google</a>
      <a href="{review_url}" target="_blank" rel="noopener">Leave a Review</a>
    </div>
    <div style="margin-top:12px" class="mini">© 2026 Lakefront Leak & Drain</div>
  </div>
</footer>
<script src="/script.js"></script>
<script id="housecall-pro-chat-bubble" src="https://chat.housecallpro.com/proChat.js" type="text/javascript" data-color="#0E6FBE" data-organization="aa9ee30f-5067-4503-b47e-febb782c4e8f" defer></script>
</body>
</html>
'''
    page_dir = root / slug
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir/'index.html').write_text(html, encoding='utf-8')

# Alias/redirect for the user-requested mixed-case path
redir = root / '_redirects'
text = redir.read_text(encoding='utf-8')
rule = '/plumbing-repair-Cleveland/* /plumbing-repair-cleveland/:splat 301\n'
if rule not in text:
    redir.write_text(text + ('\n' if not text.endswith('\n') else '') + rule, encoding='utf-8')

# Create uppercase path page too for convenience with canonical lower-case
upper_dir = root / 'plumbing-repair-Cleveland'
upper_dir.mkdir(exist_ok=True)
upper_html = (root/'plumbing-repair-cleveland'/'index.html').read_text(encoding='utf-8').replace('https://lakefrontleakanddrain.com/plumbing-repair-cleveland/', 'https://lakefrontleakanddrain.com/plumbing-repair-cleveland/')
(upper_dir/'index.html').write_text(upper_html, encoding='utf-8')

# Update services page with featured Cleveland SEO pages section if missing
services = root/'services'/'index.html'
services_html = services.read_text(encoding='utf-8')
if 'Featured Cleveland service pages' not in services_html:
    insert = '''<div class="card" style="margin-top:18px"><h2>Featured Cleveland service pages</h2><p class="mini">Explore our most important Cleveland plumbing and drain service pages.</p><div style="display:flex;flex-wrap:wrap"><a class="button ghost" style="margin:6px 6px 0 0" href="/leak-repair-cleveland/">Leak Repair</a><a class="button ghost" style="margin:6px 6px 0 0" href="/drain-cleaning-cleveland/">Drain Cleaning</a><a class="button ghost" style="margin:6px 6px 0 0" href="/sump-pump-repair-cleveland/">Sump Pump Repair</a><a class="button ghost" style="margin:6px 6px 0 0" href="/sump-pump-inspection-cleveland/">Sump Pump Inspection</a><a class="button ghost" style="margin:6px 6px 0 0" href="/basement-flooding-cleveland/">Basement Flooding Help</a><a class="button ghost" style="margin:6px 6px 0 0" href="/clogged-drain-cleveland/">Clogged Drain Repair</a><a class="button ghost" style="margin:6px 6px 0 0" href="/plumbing-repair-cleveland/">Plumbing Repair</a><a class="button ghost" style="margin:6px 6px 0 0" href="/water-pressure-problems-cleveland/">Water Pressure Problems</a><a class="button ghost" style="margin:6px 6px 0 0" href="/sewer-smell-basement-cleveland/">Sewer Smell in Basement</a><a class="button ghost" style="margin:6px 6px 0 0" href="/leaking-pipe-repair-cleveland/">Leaking Pipe Repair</a></div></div>'''
    services_html = services_html.replace('</div>\n            </div>\n        </section>', insert + '\n            </div>\n        </section>', 1)
    services.write_text(services_html, encoding='utf-8')

# Update home page with a quick featured links card if missing
home = root/'index.html'
home_html = home.read_text(encoding='utf-8')
if 'Popular Cleveland plumbing pages' not in home_html:
    marker = '<div class="grid" style="margin-top:16px">'
    # add card after first services grid closing
    pattern = re.compile(r'(</div>\s*</section>)', re.M)
    # only replace first occurrence after services heading
    services_pos = home_html.find('<h2 class="section-title">Services</h2>')
    if services_pos != -1:
        end_pos = home_html.find('</section>', services_pos)
        if end_pos != -1:
            card = '\n                <div class="card" style="margin-top:16px">\n                    <h3>Popular Cleveland plumbing pages</h3>\n                    <div style="display:flex;flex-wrap:wrap">\n                        <a class="button ghost" style="margin:6px 6px 0 0" href="/leak-repair-cleveland/">Leak Repair</a>\n                        <a class="button ghost" style="margin:6px 6px 0 0" href="/drain-cleaning-cleveland/">Drain Cleaning</a>\n                        <a class="button ghost" style="margin:6px 6px 0 0" href="/sump-pump-repair-cleveland/">Sump Pump Repair</a>\n                        <a class="button ghost" style="margin:6px 6px 0 0" href="/basement-flooding-cleveland/">Basement Flooding Help</a>\n                        <a class="button ghost" style="margin:6px 6px 0 0" href="/plumbing-repair-cleveland/">Plumbing Repair</a>\n                    </div>\n                </div>\n'
            home_html = home_html[:end_pos] + card + home_html[end_pos:]
            home.write_text(home_html, encoding='utf-8')

# Update sitemap
sitemap = root/'sitemap.xml'
s = sitemap.read_text(encoding='utf-8')
for slug in list(pages.keys()) + ['plumbing-repair-Cleveland']:
    loc = f'https://lakefrontleakanddrain.com/{slug}/'
    if loc not in s:
        add = f'  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>\n'
        s = s.replace('</urlset>', add + '</urlset>')
sitemap.write_text(s, encoding='utf-8')
print('Generated', len(pages), 'pages and updated sitemap/services/home.')
