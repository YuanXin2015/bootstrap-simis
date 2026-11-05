"""Build a dependency-free, accessible static workshop website from workshop.json."""
from pathlib import Path
from datetime import date
from html import escape
from urllib.parse import urlsplit, unquote
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

def session_html(s):
    time=esc(s.get('time','Time TBA'))
    speaker=esc(s.get('speaker',''))
    affiliation=esc(s.get('affiliation',''))
    author=f'<p class="session-speaker">{speaker}'+(f' <span>· {affiliation}</span>' if affiliation else '')+'</p>' if speaker else ''
    abstract=f'<details><summary>Abstract</summary><p>{esc(s["abstract"])}</p></details>' if s.get('abstract') else ''
    resources=''.join(resource_link(r) for r in s.get('resources',[]))
    return f'<article class="session"><p class="session-time">{time}</p><div><h4>{esc(s["title"])}</h4>{author}{abstract}'+(f'<div class="resources">{resources}</div>' if resources else '')+'</div></article>'

def participant_html(p):
    return f'<tr><th scope="row">{esc(p["name"])}</th><td class="chinese" lang="zh">{esc(p["name_zh"])}</td><td>{esc(p["affiliation"])}</td></tr>'

def build():
    data=json.loads((ROOT/'workshop.json').read_text())
    poster_version=hashlib.sha256((ROOT/'attachments/bootstrap-workshop-poster.pdf').read_bytes()).hexdigest()[:12]
    days=data['days']
    agenda=[];day_links=[]
    for i,day in enumerate(days):
        dt=date.fromisoformat(day['date'])
        key='day-'+day['date']
        day_links.append(f'<a href="#{key}"><span>DAY {i+1:02}</span>{dt.day} November</a>')
        sessions=''.join(session_html(s) for s in day['sessions'])
        if not sessions:sessions='<div class="agenda-pending"><span class="status-dot" aria-hidden="true"></span><div><h4>Programme to be announced</h4><p>Talk titles, speakers, and session times will appear here.</p></div></div>'
        agenda.append(f'<section class="agenda-day" id="{key}" aria-labelledby="{key}-heading"><div class="day-heading"><h3 id="{key}-heading">{dt.strftime("%A")} <span>{dt.day} November</span></h3><span class="eyebrow">DAY {i+1:02}</span></div>{sessions}</section>')
    people=sorted(data['participants'],key=lambda p:(p['name'].split()[-1].lower(),p['name'].lower()))
    participant_rows=''.join(participant_html(p) for p in people)
    paragraphs=''.join(f'<p>{esc(p)}</p>' for p in data['overview'])
    themes=''.join(f'<li>{esc(t)}</li>' for t in data['themes'])
    venue=data['venue']
    organizers=''.join(f'<p>{esc(o["name"])} <span lang="zh">{esc(o["name_zh"])}</span></p>' for o in data['organizers'])
    html=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bootstrap Workshop 2026 · SIMIS, Shanghai</title>
<meta name="description" content="Bootstrap methods in theoretical physics. 22–24 November 2026 at SIMIS, Shanghai. Overview, programme, participants, and practical information.">
<meta name="theme-color" content="#e9eee5"><link rel="icon" href="assets/simis-symbol.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/style.css">
</head><body><a class="skip" href="#main">Skip to content</a>
<header class="masthead wrap"><a class="brand" href="#top" aria-label="SIMIS Bootstrap Workshop home"><img src="assets/simis-symbol.svg" width="44" height="44" alt=""><span>SIMIS</span></a><nav aria-label="Main navigation"><a href="#overview">Overview</a><a href="#agenda">Agenda</a><a href="#participants">Participants</a><a href="#logistics">Logistics</a></nav></header>
<main id="main"><section class="hero wrap" id="top"><div class="hero-top"><p class="eyebrow">A WORKSHOP IN THEORETICAL PHYSICS</p><p class="eyebrow">SHANGHAI · 2026</p></div><h1>{esc(data['title'])}</h1><div class="hero-meta"><p>22–24 November 2026</p><span aria-hidden="true"></span><p>SIMIS · 18th floor</p><a class="registration-link" href="#registration">Registration</a></div><img class="tower-art" src="assets/tower-equation.svg" width="1020" height="525" alt="Two forms of the Oriental Pearl Tower equated above a continuous Shanghai skyline."><div class="hero-bottom"><a href="#agenda">Explore the programme <span aria-hidden="true">↓</span></a></div></section>
<section id="overview" class="section wrap two-column"><div><p class="eyebrow">01 / OVERVIEW</p><h2>Overview</h2></div><div class="prose">{paragraphs}<h3 class="eyebrow topics-heading">SCIENTIFIC THEMES</h3><ul class="themes">{themes}</ul><div id="registration"><h3 class="eyebrow topics-heading">PARTICIPATION &amp; REGISTRATION</h3><p>The workshop will be held in person, and we warmly encourage people to join us. Registration is free.</p><p>To register, please email <a href="mailto:yuan.xin.bot@gmail.com">yuan.xin.bot@gmail.com</a> with the following details:</p><ul><li>Name</li><li>Affiliation</li><li>Department and academic position</li><li>Phone number</li><li>Email address</li></ul><p>We will use these details to arrange your access to SIMIS during the event. We look forward to seeing many of you there!</p></div></div></section>
<section id="agenda" class="section wrap"><div class="section-top"><div><p class="eyebrow">02 / AGENDA</p><h2>The Programme</h2></div><p class="section-note">All times are China Standard Time<br>UTC+8 · Shanghai</p></div><nav class="day-nav" aria-label="Programme days">{''.join(day_links)}</nav><div class="agenda">{''.join(agenda)}</div><p class="fine">Slides, notes, and recording links will be added to individual talks as they become available.</p></section>
<section id="participants" class="section wrap"><div class="section-top"><div><p class="eyebrow">03 / PEOPLE</p><h2 id="participants-heading">Participants list</h2></div><p class="section-note">Participants are tentative</p></div><p class="table-hint">Scroll horizontally to see all columns.</p><div class="table-scroll" role="region" aria-labelledby="participants-heading" tabindex="0"><table class="participants-table"><colgroup><col class="name-column"><col class="chinese-column"><col class="affiliation-column"></colgroup><thead><tr><th scope="col">Name <span>(EN)</span></th><th scope="col">Name <span>(CN)</span></th><th scope="col">Affiliation</th></tr></thead><tbody>{participant_rows}</tbody></table></div></section>
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
