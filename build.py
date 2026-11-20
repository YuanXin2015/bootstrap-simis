"""Build a dependency-free, accessible static workshop website from workshop.json."""
from pathlib import Path
from datetime import date
from html import escape
from urllib.parse import urlsplit, unquote, quote
import json
import hashlib
import shutil

ROOT = Path(__file__).resolve().parent

def esc(value):
    return escape(str(value), quote=True)

def resource_link(resource):
    url=resource['url'].strip()
    parts=urlsplit(url)
    if parts.scheme:
        if parts.scheme not in ('https','http') or not parts.netloc:
            raise ValueError(f'Unsupported resource URL: {url}')
    else:
        path=unquote(parts.path)
        if parts.netloc or not path or path.startswith('/') or '\\' in path:
            raise ValueError('Use a relative attachment path or an HTTPS URL')
        target=(ROOT/path).resolve()
        if ROOT not in target.parents or not target.is_file():
            raise ValueError(f'Attachment does not exist: {url}')
        if not path.startswith('attachments/'):
            raise ValueError('Local resources must be in attachments/')
    label=resource.get('label','Resource')
    return f'<a class="resource" href="{esc(url)}">{esc(label)} <span aria-hidden="true">↗</span></a>'

def session_content(s):
    names=''.join(f'<p class="talk-name">{esc(p["name"])} <span lang="zh">{esc(p.get("name_zh", ""))}</span></p>' for p in s.get('speakers', []))
    speaker=esc(s.get('speaker',''))
    affiliation=esc(s.get('affiliation',''))
    author=f'<p class="session-speaker">{speaker}'+(f' <span>· {affiliation}</span>' if affiliation else '')+'</p>' if speaker else ''
    title_text=s.get('title') or ('TBA' if names or speaker else '')
    title_label=esc(title_text)
    if s.get('_detail_id'):
        title_label=f'<a class="talk-link" href="#{s["_detail_id"]}">{title_label}</a>'
    title=f'<h4>{title_label}</h4>' if title_text else ''
    return title+names+author

def talk_details_html(data):
    by_name={p['name']:p for p in data['participants']}
    by_zh={p['name_zh']:p for p in data['participants'] if p.get('name_zh')}
    sections=[]
    for day in data['days']:
        talks=[]
        for s in day['sessions']:
            if not s.get('_detail_id'): continue
            authors=[]
            speakers=s.get('speakers') or [{'name':s['speaker'],'affiliation':s.get('affiliation','')}]
            for p in speakers:
                record=by_zh.get(p.get('name_zh')) or by_name.get(p['name'],{})
                affiliation=p.get('affiliation') or record.get('affiliation') or s.get('affiliation') or 'Affiliation TBA'
                zh=f' <span lang="zh">{esc(p["name_zh"])}</span>' if p.get('name_zh') else ''
                authors.append(f'<span class="detail-speaker">{esc(p["name"])}{zh} <span class="detail-affiliation">({esc(affiliation)})</span></span>')
            abstract=esc(s.get('abstract') or 'Abstract forthcoming.')
            resources=''.join(resource_link(r) for r in s.get('resources',[]))
            talks.append(f'<details class="talk-detail" id="{s["_detail_id"]}"><summary><span class="detail-time">{esc(s.get("time","Time TBA"))}</span><span class="detail-description"><span class="detail-title">{esc(s.get("title") or "TBA")}</span>{"".join(authors)}</span><span class="detail-toggle" aria-hidden="true">+</span></summary><div class="detail-body"><h5>Abstract</h5><p>{abstract}</p>'+ (f'<div class="resources">{resources}</div>' if resources else '')+'</div></details>')
        if talks:
            dt=date.fromisoformat(day['date'])
            sections.append(f'<section class="talk-detail-day" aria-labelledby="details-{day["date"]}"><h4 id="details-{day["date"]}">{dt.strftime("%A")} <span>{dt.day} November</span></h4>{"".join(talks)}</section>')
    if not sections: return ''
    return '<section class="talk-details" id="talk-details" aria-labelledby="talk-details-heading"><div class="section-top"><h3 id="talk-details-heading">Talk details</h3><p class="section-note">Select a talk to read its abstract.<br>All times are China Standard Time · UTC+8</p></div>'+''.join(sections)+'</section>'

def session_html(s):
    kind=' session-break' if s.get('kind') == 'break' else ''
    return f'<article class="session{kind}"><p class="session-time">{esc(s.get("time", "Time TBA"))}</p><div>{session_content(s)}</div></article>'

def timetable_html(days):
    """Align sessions by time, leaving other days blank for day-specific events."""
    if any(not s.get('time') for day in days for s in day['sessions']):
        return ''
    times=sorted({s['time'] for day in days for s in day['sessions']})
    if not times: return ''
    by_day=[{s['time']:s for s in day['sessions']} for day in days]
    headers=''.join(f'<th scope="col"><span class="timetable-date">{date.fromisoformat(day["date"]).day} November</span><span class="timetable-weekday">{date.fromisoformat(day["date"]).strftime("%A")}</span></th>' for day in days)
    rows=[]
    for time in times:
        sessions=[sessions_by_time.get(time,{}) for sessions_by_time in by_day]
        kind=' class="timetable-break"' if all(s.get('kind') == 'break' for s in sessions) else ''
        cells=''.join(f'<td>{session_content(s)}</td>' for s in sessions)
        rows.append(f'<tr{kind}><th scope="row">{esc(time)}</th>{cells}</tr>')
    return f'<div class="timetable-desktop"><table class="timetable"><caption class="sr-only">Workshop timetable, 22–24 November 2026. All times are China Standard Time (UTC+8).</caption><thead><tr><th scope="col">Time <span class="timetable-weekday">UTC+8</span></th>{headers}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'

def participant_html(p):
    return f'<tr><th scope="row">{esc(p["name"])}</th><td class="chinese" lang="zh">{esc(p["name_zh"])}</td><td>{esc(p["affiliation"])}</td></tr>'

def participant_groups(data):
    speakers=[p for day in data['days'] for s in day['sessions'] for p in s.get('speakers', [])]
    speaker_names={p['name'] for p in speakers}
    speaker_names_zh={p['name_zh'] for p in speakers if p.get('name_zh')}
    people=sorted(data['participants'],key=lambda p:(p['name'].split()[-1].lower(),p['name'].lower()))
    shown=[];more=[]
    for p in people:
        group=shown if p.get('featured') or p['name'] in speaker_names or p.get('name_zh') in speaker_names_zh else more
        group.append(p)
    return shown,more

def participants_table(people, label):
    rows=''.join(participant_html(p) for p in people)
    return f'<div class="table-scroll" role="region" aria-label="{esc(label)}" tabindex="0"><table class="participants-table"><colgroup><col class="name-column"><col class="chinese-column"><col class="affiliation-column"></colgroup><thead><tr><th scope="col">Name <span>(EN)</span></th><th scope="col">Name <span>(CN)</span></th><th scope="col">Affiliation</th></tr></thead><tbody>{rows}</tbody></table></div>'

def build():
    data=json.loads((ROOT/'workshop.json').read_text())
    style_version=hashlib.sha256((ROOT/'assets/style.css').read_bytes()).hexdigest()[:12]
    poster_version=hashlib.sha256((ROOT/'attachments/bootstrap-workshop-poster.pdf').read_bytes()).hexdigest()[:12]
    days=data['days']
    for day in days:
        for i,s in enumerate(day['sessions']):
            if s.get('speakers') or s.get('speaker'):
                s['_detail_id']=f'talk-{day["date"]}-{i+1:02}'
    talk_details=talk_details_html(data)
    math_scripts=''
    if any('$' in s.get('abstract','') for day in days for s in day['sessions']):
        math_scripts='''<script>window.MathJax = {tex: {inlineMath: {'[+]': [['$', '$']]}}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js"></script>'''
    agenda=[];day_links=[]
    for i,day in enumerate(days):
        dt=date.fromisoformat(day['date'])
        key='day-'+day['date']
        day_links.append(f'<a href="#{key}"><span>DAY {i+1:02}</span>{dt.day} November</a>')
        sessions=''.join(session_html(s) for s in day['sessions'])
        if not sessions:sessions='<div class="agenda-pending"><span class="status-dot" aria-hidden="true"></span><div><h4>Programme to be announced</h4><p>Talk titles, speakers, and session times will appear here.</p></div></div>'
        agenda.append(f'<section class="agenda-day" id="{key}" aria-labelledby="{key}-heading"><div class="day-heading"><h3 id="{key}-heading">{dt.strftime("%A")} <span>{dt.day} November</span></h3><span class="eyebrow">DAY {i+1:02}</span></div>{sessions}</section>')
    shown_people,more_people=participant_groups(data)
    timetable=timetable_html(days)
    daily_class='agenda-mobile' if timetable else 'agenda-daily'
    programme_note=f'<p class="programme-note">{esc(data["programme_note"])}</p>' if data.get('programme_note') else ''
    participant_list=participants_table(shown_people, 'Featured participants and speakers')
    if more_people:
        participant_list+=f'<details class="more-participants"><summary>More participants <span class="participant-count">({len(more_people)})</span></summary>{participants_table(more_people, "More participants")}</details>'
    paragraphs=''.join(f'<p>{esc(p)}</p>' for p in data['overview'])
    themes=''.join(f'<li>{esc(t)}</li>' for t in data['themes'])
    registration_subject = 'Bootstrap Workshop Registration - [Your name]'
    registration_body = '\r\n'.join([
        'Dear organizers,',
        '',
        'I would like to register for the Bootstrap Workshop at SIMIS on 22-24 November 2026.',
        'Please find my details below for access to SIMIS:',
        '',
        'Name: [Your full name]',
        'Affiliation: [Your university or institute]',
        'Department: [Your department]',
        'Academic position: [Your position]',
        'Phone number: [Your phone number]',
        'Email address: [Your email address]',
        '',
        'Thank you!',
        '[Your name]',
    ])
    registration_mailto = ('mailto:yuan.xin.bot@gmail.com?subject='
                           + quote(registration_subject, safe='')
                           + '&body=' + quote(registration_body, safe=''))
    venue=data['venue']
    organizers=''.join(f'<p>{esc(o["name"])} <span lang="zh">{esc(o["name_zh"])}</span></p>' for o in data['organizers'])
    html=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bootstrap Workshop 2026 · SIMIS, Shanghai</title>
<meta name="description" content="Bootstrap methods in theoretical physics. 22–24 November 2026 at SIMIS, Shanghai. Overview, programme, participants, and practical information.">
<meta name="theme-color" content="#e9eee5"><link rel="icon" href="assets/simis-symbol.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/style.css?v={style_version}">
{math_scripts}</head><body><a class="skip" href="#main">Skip to content</a>
<header class="masthead wrap"><a class="brand" href="#top" aria-label="SIMIS Bootstrap Workshop home"><img src="assets/simis-symbol.svg" width="44" height="44" alt=""><span>SIMIS</span></a><nav aria-label="Main navigation"><a href="#overview">Overview</a><a href="#agenda">Agenda</a><a href="#participants">Participants</a><a href="#logistics">Logistics</a></nav></header>
<main id="main"><section class="hero wrap" id="top"><div class="hero-top"><p class="eyebrow">A WORKSHOP IN THEORETICAL PHYSICS</p><p class="eyebrow">SHANGHAI · 2026</p></div><h1>{esc(data['title'])}</h1><div class="hero-meta"><p>22–24 November 2026</p><span aria-hidden="true"></span><p>SIMIS · 18th floor</p><a class="registration-link" href="#registration">Registration</a></div><img class="tower-art" src="assets/tower-equation.svg" width="1020" height="525" alt="Two forms of the Oriental Pearl Tower equated above a continuous Shanghai skyline."><div class="hero-bottom"><a href="#agenda">Explore the programme <span aria-hidden="true">↓</span></a></div></section>
<section id="overview" class="section wrap"><div class="overview-heading"><p class="eyebrow">01 / OVERVIEW</p><h2>Overview</h2></div><div class="overview-layout"><div class="prose">{paragraphs}<h3 class="eyebrow topics-heading">SCIENTIFIC THEMES</h3><ul class="themes">{themes}</ul></div><div id="registration" class="prose"><h3 class="eyebrow topics-heading">PARTICIPATION &amp; REGISTRATION</h3><p>The workshop will be held in person, and we warmly encourage people to join us. Registration is free.</p><p>To register, please email <a href="{esc(registration_mailto)}">yuan.xin.bot@gmail.com</a> with the following details:</p><ul><li>Name</li><li>Affiliation</li><li>Department and academic position</li><li>Phone number</li><li>Email address</li></ul><p>We will use these details to arrange your access to SIMIS during the event. We look forward to seeing many of you there!</p></div></div></section>
<section id="agenda" class="section wrap"><div class="section-top"><div><p class="eyebrow">02 / AGENDA</p><h2>The Programme</h2></div><p class="section-note">All times are China Standard Time<br>UTC+8 · Shanghai</p></div>{programme_note}{timetable}<div class="{daily_class}"><nav class="day-nav" aria-label="Programme days">{''.join(day_links)}</nav><div class="agenda">{''.join(agenda)}</div></div><p class="fine">Slides, notes, and recording links will be added to individual talks as they become available.</p>{talk_details}</section>
<section id="participants" class="section wrap"><div class="section-top"><div><p class="eyebrow">03 / PEOPLE</p><h2 id="participants-heading">Participants list</h2></div><p class="section-note">Participants are tentative</p></div><p class="table-hint">Scroll horizontally to see all columns.</p>{participant_list}</section>
<section id="logistics" class="section wrap"><p class="eyebrow">04 / LOGISTICS</p><h2>Meet us in Shanghai.</h2><div class="logistics-grid"><div class="venue"><p class="eyebrow">THE VENUE</p><h3>{esc(venue['name'])} <span>· {esc(venue['floor'])}</span></h3><p>{esc(venue['full_name'])}</p><address>{esc(venue['address'])}<span lang="zh">{esc(venue['address_zh'])}</span></address><a class="text-link" href="{esc(venue['url'])}">Visit SIMIS <span aria-hidden="true">↗</span></a><p class="fine">{esc(data['logistics_note'])}</p></div><div class="practical"><div><p class="eyebrow">WHEN</p><p class="large">22–24 November 2026</p><a class="text-link" href="attachments/bootstrap-workshop.ics" download>Add dates to calendar <span aria-hidden="true">↗</span></a></div><div><p class="eyebrow">ORGANIZERS</p><div class="organizers">{organizers}</div></div><div><p class="eyebrow">WORKSHOP MATERIALS</p><a class="text-link" href="attachments/bootstrap-workshop-poster.pdf?v={poster_version}">Download the poster <span aria-hidden="true">↗</span></a></div></div></div></section>
</main><footer class="wrap"><span>BOOTSTRAP · SIMIS</span><span>22–24 NOVEMBER 2026 · SHANGHAI</span><a href="#top">Back to top ↑</a></footer></body></html>'''
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    (out/'index.html').write_text(html)
    for folder in ['assets','attachments']:
        shutil.copytree(ROOT/folder,out/folder,dirs_exist_ok=True)
    (out/'.nojekyll').touch()
    ics='\r\n'.join(['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//SIMIS Bootstrap Workshop//EN','CALSCALE:GREGORIAN','BEGIN:VEVENT','UID:bootstrap-simis-2026@YuanXin2015.github.io','DTSTAMP:20261102T000000Z','DTSTART;VALUE=DATE:20261122','DTEND;VALUE=DATE:20261125','SUMMARY:Bootstrap Workshop at SIMIS','LOCATION:SIMIS - 18th floor - Shanghai','DESCRIPTION:Bootstrap methods in theoretical physics.','END:VEVENT','END:VCALENDAR',''])
    (out/'attachments/bootstrap-workshop.ics').write_bytes(ics.encode())
    print(f'Built {out}/index.html')

if __name__=='__main__':build()
