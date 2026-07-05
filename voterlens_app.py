#!/usr/bin/env python3
"""
VoterLens — Know Your Vote (single-file Flask app)

Features
- Full VoterLens front-end (hero, plan builder, timeline, badges, etc.) served as one static page
- Light/Dark theme toggle built into the page itself
- Works locally and on any WSGI host (Render, Azure App Service, etc.)

Run locally:
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python3 app.py
  # open http://127.0.0.1:8000

Render deployment:
  Build Command: pip install -r requirements.txt
  Start Command: gunicorn app:app --bind=0.0.0.0:${PORT:-8000}
"""

import os
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<title>VoterLens — Know Your Vote</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
/* ── THEME TOKENS ── */
:root{
  --bg:#03070f; --bg2:#070e1c; --bg3:#0d1526;
  --surface:rgba(255,255,255,.04); --surface2:rgba(255,255,255,.07);
  --border:rgba(255,255,255,.09); --border2:rgba(255,255,255,.15);
  --text:#f5f0e8; --text2:rgba(245,240,232,.65); --text3:rgba(245,240,232,.35);
  --red:#b91c1c; --red2:#dc2626; --red3:#ef4444; --red-glow:rgba(220,38,38,.4);
  --blue:#1e3a5f; --blue2:#1d4ed8; --blue3:#60a5fa;
  --gold:#c89b3c; --gold2:#f59e0b; --gold-glow:rgba(245,158,11,.35);
  --nav-h:64px;
  --radius:12px; --radius-sm:8px;
  --serif:"Playfair Display",Georgia,serif;
  --sans:"DM Sans",system-ui,sans-serif;
  --mono:"JetBrains Mono",monospace;
}
[data-theme="light"]{
  --bg:#f0f4ff; --bg2:#e8eeff; --bg3:#dde6ff;
  --surface:rgba(255,255,255,.7); --surface2:rgba(255,255,255,.9);
  --border:rgba(0,0,0,.1); --border2:rgba(0,0,0,.18);
  --text:#0d1526; --text2:rgba(13,21,38,.65); --text3:rgba(13,21,38,.38);
  --red-glow:rgba(220,38,38,.2); --gold-glow:rgba(245,158,11,.2);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{font-family:var(--sans);background:var(--bg);color:var(--text);overflow-x:hidden;min-height:100vh;transition:background .4s,color .4s}
a{color:inherit;text-decoration:none}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:2px}
[data-theme="light"]::-webkit-scrollbar-thumb{background:rgba(0,0,0,.15)}

/* ── BACKGROUND ── */
#bg-canvas{position:fixed;inset:0;z-index:0;width:100%;height:100%;pointer-events:none}
.bg-overlay{position:fixed;inset:0;z-index:1;pointer-events:none;background:radial-gradient(ellipse 80% 70% at 50% 40%,transparent 30%,var(--bg) 100%)}
[data-theme="light"] .bg-overlay{background:radial-gradient(ellipse 80% 70% at 50% 40%,transparent 20%,rgba(240,244,255,.85) 100%)}

/* ── NAV ── */
nav{
  position:fixed;top:0;left:0;right:0;z-index:500;
  height:var(--nav-h);display:flex;align-items:center;justify-content:space-between;
  padding:0 clamp(14px,4vw,52px);
  background:rgba(3,7,15,.75);border-bottom:1px solid var(--border);
  backdrop-filter:blur(24px) saturate(1.5);
  transition:background .4s;
}
[data-theme="light"] nav{background:rgba(240,244,255,.85)}
.nav-logo{display:flex;align-items:center;gap:10px;cursor:pointer;font-family:var(--serif);font-size:19px;font-weight:900;letter-spacing:.2px;flex-shrink:0}
.nav-badge{width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,var(--red2),var(--red));display:grid;place-items:center;font-size:13px;flex-shrink:0;box-shadow:0 0 16px var(--red-glow);animation:badge-pulse 3s ease-in-out infinite}
@keyframes badge-pulse{0%,100%{box-shadow:0 0 16px var(--red-glow)}50%{box-shadow:0 0 32px var(--red-glow),0 0 64px rgba(220,38,38,.15)}}
.nav-links{display:flex;gap:2px}
@media(max-width:680px){.nav-links{display:none}}
.nav-btn{padding:7px 14px;border-radius:var(--radius-sm);border:none;background:transparent;color:var(--text2);font-family:var(--sans);font-size:13px;font-weight:500;cursor:pointer;transition:all .2s;white-space:nowrap}
.nav-btn:hover,.nav-btn.active{color:var(--text);background:var(--surface2)}
.nav-btn.active{color:var(--gold2)}
.nav-actions{display:flex;align-items:center;gap:8px}
.theme-toggle{width:36px;height:36px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface);display:grid;place-items:center;cursor:pointer;font-size:16px;transition:all .2s;flex-shrink:0}
.theme-toggle:hover{background:var(--surface2);border-color:var(--border2)}
.nav-cta{height:36px;padding:0 18px;border-radius:var(--radius-sm);border:none;background:var(--red2);color:#fff;font-family:var(--sans);font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;box-shadow:0 0 18px var(--red-glow);transition:all .2s}
.nav-cta:hover{filter:brightness(1.12);box-shadow:0 0 28px var(--red-glow)}
/* hamburger */
.ham{display:none;flex-direction:column;gap:5px;cursor:pointer;padding:6px;border:none;background:none}
.ham span{width:20px;height:2px;background:var(--text);border-radius:1px;display:block;transition:all .25s}
@media(max-width:680px){.ham{display:flex}}
.mob-drawer{display:none;position:fixed;top:var(--nav-h);left:0;right:0;z-index:490;background:rgba(3,7,15,.98);backdrop-filter:blur(24px);padding:10px;border-bottom:1px solid var(--border);flex-direction:column;gap:4px}
[data-theme="light"] .mob-drawer{background:rgba(240,244,255,.98)}
.mob-drawer.open{display:flex}
.mob-item{padding:12px 16px;border-radius:var(--radius-sm);font-size:15px;font-weight:500;color:var(--text2);cursor:pointer;border:none;background:none;text-align:left;font-family:var(--sans);transition:all .15s}
.mob-item:hover,.mob-item.active{color:var(--text);background:var(--surface)}
.mob-item.active{color:var(--gold2)}
/* flag stripe below nav */
.flag-bar{position:fixed;top:var(--nav-h);left:0;right:0;z-index:499;height:3px;display:flex}
.fb-r{flex:1;background:var(--red2);opacity:.8}
.fb-w{flex:1;background:#f5f0e8;opacity:.6}
.fb-b{flex:1;background:var(--blue2);opacity:.8}

/* ── PAGE SYSTEM ── */
.page{display:none;min-height:calc(100vh - var(--nav-h));padding-top:var(--nav-h);position:relative;z-index:10;overflow-y:auto}
.page.active{display:block}
#pg-plan.active,#pg-timeline.active,#pg-badges.active{overflow-y:auto}

/* ── HOME: HERO ── */
.hero{
  position:relative;min-height:calc(100vh - var(--nav-h));
  display:flex;align-items:center;
  padding:60px clamp(18px,6vw,80px) 40px;
  overflow:hidden;
}
/* American flag stripes — decorative right side */
.flag-deco{position:absolute;right:0;top:0;bottom:0;width:42%;pointer-events:none;overflow:hidden}
.flag-deco::after{content:"";position:absolute;inset:0;background:linear-gradient(to right,var(--bg) 0%,transparent 55%)}
.f-stripe{position:absolute;width:100%;height:7.69%}
.f-stripe:nth-child(odd){background:rgba(185,28,28,.16)}
/* Hero content */
.hero-inner{position:relative;z-index:5;max-width:min(660px,100%)}
.hero-tag{display:inline-flex;align-items:center;gap:9px;padding:6px 14px;border-radius:4px;border:1px solid rgba(245,158,11,.3);background:rgba(245,158,11,.07);margin-bottom:28px;font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold2);animation:tag-in .8s cubic-bezier(.22,1,.36,1) .15s both}
@keyframes tag-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.tag-star{width:6px;height:6px;background:var(--gold2);clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);animation:spin-star 8s linear infinite}
@keyframes spin-star{to{transform:rotate(360deg)}}
.hero-h1{font-family:var(--serif);font-size:clamp(52px,7.5vw,110px);line-height:.9;font-weight:900;margin-bottom:8px}
.h1-l1{display:block;color:var(--text);animation:lu .9s cubic-bezier(.22,1,.36,1) .25s both}
.h1-l2{display:block;color:var(--red2);text-shadow:0 0 60px rgba(220,38,38,.5);animation:lu .9s cubic-bezier(.22,1,.36,1) .4s both}
.h1-l3{display:block;-webkit-text-stroke:1.5px rgba(245,240,232,.25);color:transparent;animation:lu .9s cubic-bezier(.22,1,.36,1) .55s both}
[data-theme="light"] .h1-l3{-webkit-text-stroke:1.5px rgba(13,21,38,.25)}
@keyframes lu{from{opacity:0;transform:translateY(44px) skewY(3deg)}to{opacity:1;transform:none}}
.hero-desc{margin-top:24px;font-size:clamp(14px,1.7vw,17px);line-height:1.65;font-weight:300;color:var(--text2);max-width:500px;animation:fi .9s ease .7s both}
@keyframes fi{from{opacity:0}to{opacity:1}}
.hero-desc strong{color:var(--text);font-weight:500}
/* PROMPT BOX */
.prompt-wrap{margin-top:32px;max-width:700px;animation:fi .9s ease .85s both}
.p-box{background:rgba(5,12,30,.85);border:1px solid var(--border2);border-radius:var(--radius);overflow:hidden;backdrop-filter:blur(28px);box-shadow:0 24px 80px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.07);transition:border-color .3s,box-shadow .3s}
[data-theme="light"] .p-box{background:rgba(255,255,255,.9);box-shadow:0 24px 80px rgba(0,0,0,.12),inset 0 1px 0 rgba(255,255,255,.8)}
.p-box:focus-within{border-color:rgba(220,38,38,.4);box-shadow:0 24px 80px rgba(0,0,0,.5),0 0 0 3px rgba(220,38,38,.1)}
.p-ta{width:100%;min-height:90px;max-height:200px;background:transparent;border:none;outline:none;color:var(--text);font-family:var(--sans);font-size:15.5px;line-height:1.6;padding:18px 20px 10px;resize:none}
.p-ta::placeholder{color:var(--text3)}
.p-bot{display:flex;align-items:center;gap:8px;padding:10px 12px;border-top:1px solid var(--border);flex-wrap:wrap}
.p-state{height:36px;min-width:155px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface);color:var(--text);font-family:var(--sans);font-size:13px;padding:0 10px;outline:none;cursor:pointer;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' fill='none'%3E%3Cpath d='M1 1l4 4 4-4' stroke='rgba(245,240,232,.5)' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 9px center;padding-right:26px;transition:border-color .2s}
[data-theme="light"] .p-state{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' fill='none'%3E%3Cpath d='M1 1l4 4 4-4' stroke='rgba(13,21,38,.4)' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E")}
.p-state option{background:#070e1c}
[data-theme="light"] .p-state option{background:#e8eeff}
.p-hints{display:flex;gap:5px;flex-wrap:wrap;flex:1}
.p-hint{padding:5px 10px;border-radius:99px;border:1px solid var(--border);background:var(--surface);color:var(--text2);font-size:11px;font-weight:500;cursor:pointer;transition:all .2s;white-space:nowrap}
.p-hint:hover{border-color:rgba(220,38,38,.35);background:rgba(220,38,38,.1);color:var(--text)}
.p-send{width:40px;height:40px;border-radius:var(--radius-sm);border:none;background:var(--red2);color:#fff;display:grid;place-items:center;cursor:pointer;flex-shrink:0;box-shadow:0 4px 18px var(--red-glow);transition:all .2s}
.p-send:hover{transform:scale(1.06);box-shadow:0 6px 28px var(--red-glow)}
.p-send svg{width:15px;height:15px}
/* Stats */
.hero-stats{display:flex;gap:clamp(20px,4vw,44px);margin-top:32px;flex-wrap:wrap;animation:fi .9s ease 1s both}
.stat-n{font-family:var(--serif);font-size:clamp(28px,3.5vw,40px);font-weight:700;color:var(--gold2);line-height:1;text-shadow:0 0 24px var(--gold-glow)}
.stat-l{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--text3);margin-top:4px}
/* Globe */
.globe-wrap{position:absolute;right:clamp(-40px,-3vw,0px);top:50%;transform:translateY(-52%);width:min(520px,42vw);height:min(520px,42vw);pointer-events:none;z-index:4;animation:fi 1.5s ease .4s both;overflow:hidden}
@media(max-width:960px){.globe-wrap{display:none}}
#globe-c{width:100%;height:100%;display:block}
/* INFOGRAPHIC SCROLL SECTION */
.info-section{position:relative;padding:80px clamp(18px,6vw,80px) 100px;overflow:hidden}
.info-section::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(to right,transparent,var(--border),transparent)}
.section-tag{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--text3);display:flex;align-items:center;gap:10px;margin-bottom:20px}
.section-tag::before{content:"";flex:0 0 22px;height:1px;background:var(--border2)}
.section-title{font-family:var(--serif);font-size:clamp(32px,4vw,52px);font-weight:700;color:var(--text);max-width:600px;line-height:1.1;margin-bottom:48px}
/* Scroll-reveal infographic cards */
.infogrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}
.info-card{
  border:1px solid var(--border);border-radius:var(--radius);
  background:var(--surface);backdrop-filter:blur(16px);
  padding:28px;position:relative;overflow:hidden;
  opacity:0;transform:translateY(32px);
  transition:opacity .7s ease,transform .7s ease,border-color .25s,box-shadow .25s;
}
.info-card.visible{opacity:1;transform:none}
.info-card:nth-child(2){transition-delay:.1s}
.info-card:nth-child(3){transition-delay:.2s}
.info-card:nth-child(4){transition-delay:.3s}
.info-card::before{content:"";position:absolute;inset:0;background:var(--card-glow,linear-gradient(135deg,rgba(220,38,38,.07),transparent));opacity:0;transition:opacity .3s}
.info-card:hover{border-color:var(--border2);box-shadow:0 16px 48px rgba(0,0,0,.3)}
.info-card:hover::before{opacity:1}
.ic-icon{font-size:28px;margin-bottom:14px}
.ic-num{font-family:var(--serif);font-size:48px;font-weight:700;color:var(--gold2);line-height:1;text-shadow:0 0 20px var(--gold-glow)}
.ic-label{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--text3);margin-top:4px;margin-bottom:14px}
.ic-desc{font-size:13px;line-height:1.6;color:var(--text2)}
/* Progress bar */
.ic-bar{height:4px;background:var(--border);border-radius:2px;margin-top:16px;overflow:hidden}
.ic-fill{height:100%;background:linear-gradient(to right,var(--red2),var(--gold2));border-radius:2px;width:0;transition:width 1.2s cubic-bezier(.22,1,.36,1)}
.info-card.visible .ic-fill{width:var(--pct,70%)}
/* QUESTION CARDS */
.q-section{padding:0 clamp(18px,6vw,80px) 80px}
.cards-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.q-card{
  border:1px solid var(--border);border-radius:var(--radius);
  background:var(--surface);backdrop-filter:blur(14px);
  padding:20px;cursor:pointer;transition:all .25s;
  position:relative;overflow:hidden;
  opacity:0;transform:translateY(20px);
  transition:opacity .5s,transform .5s,border-color .25s,box-shadow .25s;
}
.q-card.visible{opacity:1;transform:none}
.q-card::after{content:"";position:absolute;inset:0;background:linear-gradient(135deg,rgba(220,38,38,.09),transparent);opacity:0;transition:opacity .25s}
.q-card:hover{border-color:rgba(220,38,38,.3);transform:translateY(-3px)!important;box-shadow:0 16px 44px rgba(0,0,0,.3)}
.q-card:hover::after{opacity:1}
.qc-icon{font-size:22px;margin-bottom:10px}
.qc-title{font-size:14px;font-weight:600;color:var(--text);margin-bottom:4px}
.qc-desc{font-size:12px;color:var(--text3);line-height:1.4}
.qc-cta{margin-top:14px;font-family:var(--mono);font-size:10px;letter-spacing:.08em;color:rgba(220,38,38,.7);text-transform:uppercase}
/* CHAT PAGE */
#pg-chat{display:none;flex-direction:row!important;height:calc(100vh - var(--nav-h));max-height:calc(100vh - var(--nav-h));padding-top:var(--nav-h);overflow:hidden}
#pg-chat.active{display:flex!important;height:calc(100vh - var(--nav-h));max-height:calc(100vh - var(--nav-h))}
.chat-side{
  width:250px;flex-shrink:0;
  border-right:1px solid var(--border);
  background:rgba(5,12,30,.82);backdrop-filter:blur(20px);
  display:flex;flex-direction:column;padding:18px 0;overflow-y:auto;
  transition:background .4s;
}
[data-theme="light"] .chat-side{background:rgba(240,244,255,.9)}
@media(max-width:768px){
  #pg-chat.active{flex-direction:column!important}
  .chat-side{width:100%;border-right:none;border-bottom:1px solid var(--border);flex-direction:row;flex-wrap:nowrap;padding:10px 14px;gap:7px;overflow-x:auto;overflow-y:hidden}
  .side-lbl,.side-bot{display:none}
  .side-sw{width:100%;padding:0!important;margin:0!important;border:none!important}
  .side-sel{width:100%}
  .side-link{padding:7px 12px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface);white-space:nowrap;border-left:2px solid transparent!important}
}
.side-lbl{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--text3);padding:0 18px 8px}
.side-sw{padding:0 18px 16px;border-bottom:1px solid var(--border);margin-bottom:14px}
.side-sel{width:100%;height:36px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface);color:var(--text);font-family:var(--sans);font-size:13px;padding:0 10px;outline:none;cursor:pointer;transition:border-color .2s}
.side-sel option{background:#070e1c}
[data-theme="light"] .side-sel option{background:#e8eeff}
.side-link{display:flex;align-items:center;gap:10px;padding:9px 18px;font-size:12px;color:var(--text2);cursor:pointer;border-left:2px solid transparent;transition:all .15s}
.side-link:hover{color:var(--text);background:var(--surface);border-left-color:var(--red2)}
.side-link-ico{font-size:13px;width:16px;text-align:center;flex-shrink:0}
.side-bot{margin-top:auto;padding:16px 18px;border-top:1px solid var(--border)}
.emer-card{border:1px solid rgba(185,28,28,.3);border-radius:var(--radius-sm);background:rgba(185,28,28,.07);padding:12px;text-decoration:none;display:block;transition:all .2s}
.emer-card:hover{background:rgba(185,28,28,.13);border-color:rgba(220,38,38,.5)}
.emer-num{font-family:var(--serif);font-size:17px;color:var(--red3);font-weight:700;text-shadow:0 0 10px rgba(239,68,68,.4)}
.emer-sub{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--text3);margin-top:3px}
.chat-main{flex:1;display:flex;flex-direction:column;overflow:hidden;position:relative;min-width:0}
.msgs{flex:1;overflow-y:auto;padding:28px clamp(14px,4vw,44px) 140px;display:flex;flex-direction:column;gap:22px;scrollbar-width:thin;scroll-behavior:smooth;overscroll-behavior:contain}
.msg-u{align-self:flex-end;max-width:min(72%,600px);padding:13px 18px;border-radius:12px 12px 3px 12px;background:linear-gradient(135deg,var(--blue2),#1e40af);font-size:14.5px;line-height:1.6;box-shadow:0 6px 24px rgba(29,78,216,.3);word-break:break-word;animation:msg-r .35s cubic-bezier(.34,1.56,.64,1) both}
@keyframes msg-r{from{opacity:0;transform:translateX(18px) scale(.94)}to{opacity:1;transform:none}}
.msg-a{align-self:flex-start;max-width:min(92%,860px);width:100%;animation:msg-l .35s cubic-bezier(.34,1.56,.64,1) both}
@keyframes msg-l{from{opacity:0;transform:translateX(-18px) scale(.94)}to{opacity:1;transform:none}}
.msg-a-head{display:flex;align-items:center;justify-content:space-between;padding:9px 14px;background:rgba(3,7,15,.7);border:1px solid var(--border);border-bottom:none;border-radius:var(--radius) var(--radius) 0 0;flex-wrap:wrap;gap:6px}
[data-theme="light"] .msg-a-head{background:rgba(255,255,255,.8)}
.vl-badge{display:flex;align-items:center;gap:8px;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--gold2)}
.vl-icon{width:22px;height:22px;border-radius:5px;background:linear-gradient(135deg,var(--red2),var(--red));display:grid;place-items:center;font-family:var(--serif);font-size:9px;font-weight:700;box-shadow:0 0 10px var(--red-glow)}
.msg-btns{display:flex;gap:5px;flex-wrap:wrap}
.m-btn{height:24px;padding:0 9px;border-radius:4px;border:1px solid var(--border);background:transparent;color:var(--text2);font-family:var(--mono);font-size:9px;letter-spacing:.06em;cursor:pointer;transition:all .15s;white-space:nowrap}
.m-btn:hover{background:var(--surface2);color:var(--text)}
.m-btn.spk{border-color:rgba(245,158,11,.35);color:var(--gold2)}
.msg-a-body{background:rgba(5,12,30,.8);border:1px solid var(--border);border-top:none;border-radius:0 0 var(--radius) var(--radius);padding:16px 18px;font-size:14px;line-height:1.7;backdrop-filter:blur(14px);word-break:break-word;overflow:hidden}
[data-theme="light"] .msg-a-body{background:rgba(255,255,255,.85)}
.msg-a-body h2{font-family:var(--serif);font-size:18px;color:var(--gold2);margin:13px 0 6px;font-weight:700}
.msg-a-body h3{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--text3);margin:12px 0 5px}
.msg-a-body p{margin:7px 0;color:var(--text2)}
.msg-a-body ul,.msg-a-body ol{margin:7px 0 7px 20px}
.msg-a-body li{margin:5px 0;color:var(--text2)}
.msg-a-body a{color:var(--blue3)}.msg-a-body a:hover{text-decoration:underline}
.msg-a-body strong{color:var(--text);font-weight:600}
.msg-a-body hr{border:none;border-top:1px solid var(--border);margin:12px 0}
.src-chips{display:flex;flex-wrap:wrap;gap:5px;padding:9px 14px 12px;background:rgba(3,7,15,.5);border:1px solid var(--border);border-top:none;border-radius:0 0 var(--radius) var(--radius);margin-top:-1px}
[data-theme="light"] .src-chips{background:rgba(240,244,255,.6)}
.src-chip{display:inline-flex;align-items:center;gap:4px;padding:4px 9px;border-radius:4px;border:1px solid rgba(29,78,216,.25);background:rgba(29,78,216,.08);color:var(--blue3);font-size:10px;font-family:var(--mono);text-decoration:none;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;transition:all .15s}
.src-chip:hover{background:rgba(29,78,216,.18)}
.dots{display:flex;align-items:center;gap:8px;padding:6px 0;flex-wrap:nowrap;overflow:hidden}
.dots-balls{display:flex;gap:5px;flex-shrink:0}
.dots-label{font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--text3);animation:thinking-fade 1.4s ease-in-out infinite;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@keyframes thinking-fade{0%,100%{opacity:.4}50%{opacity:1}}
.dots span{width:7px;height:7px;border-radius:50%;background:var(--red2);opacity:.35;animation:dot-b 1.4s ease-in-out infinite;box-shadow:0 0 8px var(--red-glow)}
.dots span:nth-child(2){animation-delay:.22s}
.dots span:nth-child(3){animation-delay:.44s}
@keyframes dot-b{0%,80%,100%{transform:translateY(0);opacity:.3}40%{transform:translateY(-7px);opacity:1}}
.chat-welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:52vh;text-align:center;gap:14px;padding:24px}
.cw-ico{font-size:52px}.cw-h{font-family:var(--serif);font-size:30px;font-weight:700;color:var(--gold2);text-shadow:0 0 24px var(--gold-glow)}.cw-p{font-size:13px;color:var(--text3);max-width:320px;line-height:1.6}
.cw-pills{display:flex;flex-wrap:wrap;gap:7px;justify-content:center;margin-top:6px}
.cw-pill{padding:7px 14px;border-radius:4px;border:1px solid var(--border);background:var(--surface);color:var(--text2);font-size:12px;cursor:pointer;transition:all .2s}
.cw-pill:hover{border-color:rgba(220,38,38,.3);background:rgba(220,38,38,.08);color:var(--text)}
/* input bar */
.ibar-wrap{flex-shrink:0;position:relative;padding:10px clamp(12px,3vw,44px) 18px;background:linear-gradient(to top,var(--bg) 70%,transparent);z-index:10}
@media(max-width:768px){.ibar-wrap{position:relative;bottom:auto;left:auto;right:auto}}
.ibar{background:rgba(5,12,30,.92);border:1px solid var(--border2);border-radius:var(--radius);overflow:hidden;backdrop-filter:blur(22px);transition:border-color .25s,box-shadow .25s}
[data-theme="light"] .ibar{background:rgba(255,255,255,.92)}
.ibar:focus-within{border-color:rgba(220,38,38,.4);box-shadow:0 0 0 3px rgba(220,38,38,.09)}
.ibar-row{display:flex;align-items:flex-end;padding:12px 12px 12px 18px;gap:9px}
.ibar-ta{flex:1;background:transparent;border:none;outline:none;color:var(--text);font-family:var(--sans);font-size:15px;line-height:1.5;resize:none;min-height:22px;max-height:120px}
.ibar-ta::placeholder{color:var(--text3)}
.ibar-btns{display:flex;gap:7px;align-items:center}
.i-mic{width:34px;height:34px;border-radius:var(--radius-sm);border:1px solid var(--border);background:transparent;color:var(--text2);display:grid;place-items:center;cursor:pointer;font-size:15px;transition:all .2s}
.i-mic:hover{background:var(--surface2);color:var(--text)}
.i-mic.on{border-color:rgba(70,211,139,.4);background:rgba(70,211,139,.08);color:#46d38b}
.i-send{width:34px;height:34px;border-radius:var(--radius-sm);border:none;background:var(--red2);color:#fff;display:grid;place-items:center;cursor:pointer;box-shadow:0 4px 14px var(--red-glow);transition:all .2s;flex-shrink:0}
.i-send:hover{transform:scale(1.06);filter:brightness(1.1)}
.i-send svg{width:14px;height:14px}
.ibar-foot{padding:0 18px 10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px}
.ibar-note{font-family:var(--mono);font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:var(--text3)}
.ibar-emer{font-family:var(--mono);font-size:9px;letter-spacing:.06em;color:rgba(185,28,28,.7);text-decoration:none}
.ibar-emer:hover{color:var(--red3)}
/* ABOUT */
#pg-about{overflow-y:visible}
.about-hero{position:relative;padding:clamp(50px,7vh,90px) clamp(18px,6vw,80px);overflow:hidden;display:flex;align-items:center}
.about-flag-top{position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(to right,var(--red2) 0%,var(--red2) 33.3%,#f5f0e8 33.3%,#f5f0e8 66.6%,var(--blue2) 66.6%,var(--blue2) 100%)}
.about-bg-glow{position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse 55% 80% at 20% 50%,rgba(185,28,28,.09),transparent),radial-gradient(ellipse 45% 60% at 80% 30%,rgba(29,78,216,.07),transparent)}
.about-inner{position:relative;z-index:2;display:flex;align-items:center;gap:clamp(28px,5vw,72px);flex-wrap:wrap}
/* Photo */
.photo-frame{flex-shrink:0;position:relative;width:clamp(190px,20vw,248px);height:clamp(190px,20vw,248px)}
.photo-ring1{position:absolute;inset:-14px;border-radius:50%;border:1px solid rgba(220,38,38,.35);animation:ring-spin 12s linear infinite}
.photo-ring2{position:absolute;inset:-28px;border-radius:50%;border:1px dashed rgba(245,158,11,.22);animation:ring-spin 20s linear infinite reverse}
@keyframes ring-spin{to{transform:rotate(360deg)}}
.photo-dot{position:absolute;width:8px;height:8px;border-radius:50%;background:var(--red2);box-shadow:0 0 12px var(--red2);top:50%;left:-14px;transform:translateY(-50%)}
.photo-dot2{position:absolute;width:6px;height:6px;border-radius:50%;background:var(--gold2);box-shadow:0 0 8px var(--gold2);bottom:-28px;left:50%;transform:translateX(-50%)}
.photo-img{width:100%;height:100%;border-radius:50%;border:3px solid rgba(255,255,255,.14);object-fit:cover;object-position:center 15%;box-shadow:0 0 50px rgba(220,38,38,.18),0 20px 60px rgba(0,0,0,.5);display:block}
/* About text */
.about-txt{flex:1;min-width:240px}
.about-eyebrow{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold2);margin-bottom:14px;display:flex;align-items:center;gap:10px}
.about-eyebrow::before{content:"";width:22px;height:1px;background:var(--gold2)}
.about-name{font-family:var(--serif);font-size:clamp(40px,5vw,66px);font-weight:900;line-height:.92;color:var(--text);margin-bottom:10px}
.about-role{font-size:clamp(13px,1.6vw,16px);color:var(--text2);font-weight:300;margin-bottom:20px}
.about-role strong{color:var(--red3);font-weight:600}
.about-bio{font-size:clamp(13px,1.4vw,15px);line-height:1.7;color:var(--text2);max-width:500px}
/* Mission quote */
.mission{border:1px solid rgba(245,158,11,.2);border-radius:var(--radius);background:rgba(245,158,11,.05);padding:clamp(22px,3vw,38px) clamp(22px,4vw,48px);margin:0 clamp(18px,6vw,80px) clamp(32px,5vh,64px);display:flex;align-items:center;gap:36px;flex-wrap:wrap}
.mission-q{font-family:var(--serif);font-size:clamp(16px,2vw,21px);font-style:italic;color:var(--text);line-height:1.45;flex:1;min-width:220px}
.mission-q::before{content:"\201C";font-size:50px;color:var(--gold2);line-height:0;vertical-align:-.4em;margin-right:6px}
.mission-who{flex-shrink:0;text-align:center;border-left:1px solid var(--border);padding-left:36px}
@media(max-width:600px){.mission-who{border-left:none;border-top:1px solid var(--border);padding-left:0;padding-top:18px;width:100%}}
.m-name{font-family:var(--serif);font-size:16px;font-weight:700;color:var(--gold2)}.m-role{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--text3);margin-top:4px}
/* About grid */
.about-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:clamp(14px,2vw,26px);margin:0 clamp(18px,6vw,80px) clamp(40px,6vh,80px)}
.about-card{border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);backdrop-filter:blur(14px);padding:clamp(18px,2.5vw,28px);transition:all .25s;opacity:0;transform:translateY(24px);transition:opacity .6s,transform .6s,border-color .25s}
.about-card.visible{opacity:1;transform:none}
.about-card:hover{border-color:var(--border2);box-shadow:0 12px 40px rgba(0,0,0,.25)}
.ac-tag{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--text3);margin-bottom:13px;display:flex;align-items:center;gap:10px}
.ac-tag::before{content:"";flex:0 0 14px;height:1px;background:var(--border2)}
.ac-h{font-family:var(--serif);font-size:clamp(18px,2.2vw,24px);font-weight:700;color:var(--text);margin-bottom:12px;line-height:1.1}
.ac-b{font-size:13.5px;line-height:1.75;color:var(--text2)}
.ac-b p{margin:7px 0}.ac-b strong{color:var(--text);font-weight:600}.ac-b ul{margin:7px 0 7px 18px}.ac-b li{margin:5px 0}

/* ── BATTLEGROUND GLOBE SECTION ── */
.globe-section{
  position:relative;z-index:10;
  background:linear-gradient(180deg,var(--bg) 0%,rgba(5,12,30,.6) 40%,rgba(5,12,30,.6) 60%,var(--bg) 100%);
  padding:0 0 80px;
  overflow:hidden;
}
[data-theme="light"] .globe-section{
  background:linear-gradient(180deg,var(--bg) 0%,rgba(220,230,255,.5) 40%,rgba(220,230,255,.5) 60%,var(--bg) 100%);
}
.globe-section-inner{
  max-width:1400px;margin:0 auto;
  padding:0 clamp(18px,6vw,80px);
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:40px;
  align-items:center;
}
@media(max-width:900px){
  .globe-section-inner{grid-template-columns:1fr;gap:24px}
  .globe-3d-wrap{order:-1}
}
/* Left: globe canvas */
.globe-3d-wrap{
  position:relative;
  width:100%;
  aspect-ratio:1/1;
  max-width:560px;
  margin:0 auto;
}
#battle-globe{width:100%;height:100%;display:block;border-radius:50%}
/* Pulse rings behind globe */
.globe-rings{position:absolute;inset:0;pointer-events:none;display:flex;align-items:center;justify-content:center}
.g-ring{position:absolute;border-radius:50%;border:1px solid rgba(220,38,38,.18);animation:ring-out 3.5s ease-out infinite}
.g-ring:nth-child(2){animation-delay:1.2s;border-color:rgba(245,158,11,.12)}
.g-ring:nth-child(3){animation-delay:2.4s;border-color:rgba(29,78,216,.12)}
@keyframes ring-out{0%{width:50%;height:50%;opacity:.7}100%{width:160%;height:160%;opacity:0}}
/* Right: info panel */
.globe-info{display:flex;flex-direction:column;gap:20px}
.globe-headline{font-family:var(--serif);font-size:clamp(26px,3.5vw,44px);font-weight:700;color:var(--text);line-height:1.05;margin-bottom:6px}
.globe-sub{font-size:14px;color:var(--text2);line-height:1.65;max-width:480px;margin-bottom:8px}
/* Legend chips */
.legend{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.leg-chip{display:flex;align-items:center;gap:6px;padding:5px 12px;border-radius:99px;font-family:var(--mono);font-size:10px;letter-spacing:.06em;border:1px solid var(--border)}
.leg-chip .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.leg-r{background:rgba(220,38,38,.1);border-color:rgba(220,38,38,.25);color:var(--red3)}
.leg-r .dot{background:var(--red2);box-shadow:0 0 6px var(--red2)}
.leg-b{background:rgba(29,78,216,.1);border-color:rgba(29,78,216,.25);color:var(--blue3)}
.leg-b .dot{background:var(--blue2);box-shadow:0 0 6px var(--blue2)}
.leg-swing{background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.3);color:var(--gold2)}
.leg-swing .dot{background:var(--gold2);box-shadow:0 0 6px var(--gold2)}
/* State cards */
.state-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}
.state-card{
  border:1px solid var(--border);border-radius:10px;
  background:var(--surface);backdrop-filter:blur(12px);
  padding:14px 16px;cursor:pointer;
  transition:all .25s;
  display:flex;align-items:flex-start;gap:10px;
}
.state-card:hover{transform:translateY(-2px);box-shadow:0 12px 36px rgba(0,0,0,.25)}
.sc-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;margin-top:4px}
.sc-info{}
.sc-name{font-size:13px;font-weight:600;color:var(--text)}
.sc-ev{font-family:var(--mono);font-size:10px;color:var(--text3);margin-top:2px}
.sc-status{font-size:11px;margin-top:4px;font-weight:500}
.sc-t-swing{color:var(--gold2)}
.sc-t-lean-r{color:var(--red3)}
.sc-t-lean-b{color:var(--blue3)}
.state-card.sc-swing{border-color:rgba(245,158,11,.25)}
.state-card.sc-swing:hover{border-color:rgba(245,158,11,.5);box-shadow:0 12px 36px rgba(245,158,11,.1)}
.state-card.sc-lean-r{border-color:rgba(220,38,38,.2)}
.state-card.sc-lean-r:hover{border-color:rgba(220,38,38,.45);box-shadow:0 12px 36px rgba(220,38,38,.1)}
.state-card.sc-lean-b{border-color:rgba(29,78,216,.2)}
.state-card.sc-lean-b:hover{border-color:rgba(29,78,216,.45);box-shadow:0 12px 36px rgba(29,78,216,.1)}
/* Tooltip on globe hover */
.globe-tooltip{
  position:absolute;bottom:18px;left:50%;transform:translateX(-50%);
  background:rgba(5,12,30,.92);border:1px solid var(--border2);
  border-radius:var(--radius-sm);padding:8px 14px;
  font-family:var(--mono);font-size:11px;
  color:var(--text);letter-spacing:.04em;
  pointer-events:none;white-space:nowrap;
  opacity:0;transition:opacity .25s;
  backdrop-filter:blur(14px);
  z-index:20;
}
.globe-tooltip.show{opacity:1}

/* ── 3D USA MAP SECTION ── */
.map-section{
  position:relative;z-index:10;
  padding:80px clamp(18px,6vw,80px) 90px;
  overflow:hidden;
}
.map-section::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(to right,transparent,var(--border),transparent)}
.map-header{text-align:center;margin-bottom:36px}
.map-header .section-tag{justify-content:center;margin-bottom:12px}
.map-title{font-family:var(--serif);font-size:clamp(28px,4vw,52px);font-weight:700;color:var(--text);line-height:1.05;margin-bottom:10px}
.map-sub{font-size:15px;color:var(--text2);max-width:560px;margin:0 auto;line-height:1.6}

/* Map container */
.map-stage{
  position:relative;
  width:100%;max-width:1100px;margin:0 auto;
  height:clamp(420px,48vw,580px);
  border-radius:20px;
  border:1px solid rgba(0,0,0,0.12);
  background:#e8eef5;
  box-shadow:0 8px 40px rgba(0,0,0,0.25);
  overflow:hidden;
  box-shadow:0 32px 100px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.05);
}
[data-theme="light"] .map-stage{background:rgba(220,230,255,.4)}
#map-canvas{width:100%;height:100%;display:block;cursor:default;position:absolute;top:0;left:0}
#map-canvas.hovering{cursor:pointer}

/* Tooltip */
#map-tooltip{
  position:absolute;
  pointer-events:none;
  z-index:50;
  background:rgba(4,10,26,.95);
  border:1px solid var(--border2);
  border-radius:10px;
  padding:14px 18px;
  min-width:240px;
  max-width:320px;
  backdrop-filter:blur(20px);
  box-shadow:0 16px 48px rgba(0,0,0,.6);
  opacity:0;transition:opacity .2s ease;
  transform:translateY(6px);
  transition:opacity .2s,transform .2s;
}
#map-tooltip.show{opacity:1;transform:translateY(0)}
[data-theme="light"] #map-tooltip{background:rgba(240,244,255,.97)}
.tt-state{font-family:var(--serif);font-size:18px;font-weight:700;color:var(--text);margin-bottom:2px}
.tt-abbr{font-family:var(--mono);font-size:10px;letter-spacing:.1em;color:var(--text3);text-transform:uppercase;margin-bottom:10px}
.tt-row{display:flex;align-items:center;gap:8px;margin:5px 0;font-size:12px;color:var(--text2)}
.tt-icon{font-size:14px;width:18px;flex-shrink:0}
.tt-val{color:var(--text);font-weight:500}
.tt-lean{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:99px;font-family:var(--mono);font-size:10px;font-weight:600;margin-top:6px;letter-spacing:.05em}
.tt-swing{background:rgba(245,158,11,.15);border:1px solid rgba(245,158,11,.3);color:var(--gold2)}
.tt-lean-r{background:rgba(220,38,38,.12);border:1px solid rgba(220,38,38,.3);color:var(--red3)}
.tt-lean-b{background:rgba(29,78,216,.12);border:1px solid rgba(29,78,216,.3);color:var(--blue3)}
.tt-solid-r{background:rgba(185,28,28,.1);border:1px solid rgba(185,28,28,.25);color:#f87171}
.tt-solid-b{background:rgba(29,78,216,.08);border:1px solid rgba(29,78,216,.2);color:#93c5fd}
.tt-cta{margin-top:12px;padding:8px 0 0;border-top:1px solid var(--border);font-family:var(--mono);font-size:10px;letter-spacing:.08em;color:rgba(220,38,38,.75);text-transform:uppercase}

/* Map legend */
.map-legend{
  display:flex;align-items:center;justify-content:center;
  gap:clamp(10px,2vw,24px);margin-top:20px;flex-wrap:wrap;
}
.ml-item{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10px;letter-spacing:.06em;color:var(--text2)}
.ml-dot{width:12px;height:12px;border-radius:3px;flex-shrink:0}
.ml-r{background:#dc2626;box-shadow:0 0 8px rgba(220,38,38,.6)}
.ml-b{background:#1d4ed8;box-shadow:0 0 8px rgba(29,78,216,.6)}
.ml-swing{background:#f59e0b;box-shadow:0 0 8px rgba(245,158,11,.6)}
.ml-hover{background:rgba(255,255,255,.3)}

/* Controls */
.map-controls{
  display:flex;align-items:center;justify-content:center;
  gap:10px;margin-top:16px;flex-wrap:wrap;
}
.mc-btn{
  height:32px;padding:0 16px;border-radius:var(--radius-sm);
  border:1px solid var(--border);background:var(--surface);
  color:var(--text2);font-family:var(--mono);font-size:10px;
  letter-spacing:.06em;cursor:pointer;transition:all .2s;
}
.mc-btn:hover{background:var(--surface2);color:var(--text);border-color:var(--border2)}
.mc-btn.active{background:rgba(220,38,38,.12);border-color:rgba(220,38,38,.35);color:var(--red3)}
.mc-hint{font-family:var(--mono);font-size:10px;color:var(--text3);letter-spacing:.06em}

/* ═══════════════════════════════════════════
   NEW FEATURES — CIVIC CONCEPT ENHANCEMENTS
   ═══════════════════════════════════════════ */

/* ── EMERGENCY BUTTON (floating) ── */
.emer-fab{position:fixed;bottom:clamp(20px,4vw,28px);right:clamp(16px,4vw,32px);z-index:600;display:flex;align-items:center;gap:8px;height:36px;padding:0 16px;border-radius:var(--radius-sm);background:rgba(185,28,28,.12);color:var(--red3);border:1px solid rgba(220,38,38,.35);cursor:pointer;font-family:var(--mono);font-size:10px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;backdrop-filter:blur(12px);transition:all .2s;}
.emer-fab:hover{background:rgba(220,38,38,.18);border-color:rgba(220,38,38,.55);color:var(--red3)}
.emer-fab-ico{font-size:12px;opacity:.85}

/* ── EMERGENCY MODAL ── */
.modal-backdrop{position:fixed;inset:0;z-index:800;background:rgba(3,7,15,.88);backdrop-filter:blur(16px) saturate(1.2);display:none;align-items:flex-start;justify-content:center;padding:clamp(16px,5vw,60px) 16px;overflow-y:auto;}
.modal-backdrop.open{display:flex}
.modal-box{
  background:rgba(4,10,28,.96);border:1px solid var(--border);border-radius:var(--radius);max-width:680px;width:100%;box-shadow:0 32px 80px rgba(0,0,0,.65),inset 0 1px 0 rgba(255,255,255,.05);overflow:hidden;animation:modal-in .3s cubic-bezier(.22,1,.36,1) both;}
[data-theme="light"] .modal-box{background:rgba(255,248,248,.98);border-color:rgba(220,38,38,.3)}
@keyframes modal-in{from{opacity:0;transform:translateY(24px) scale(.96)}to{opacity:1;transform:none}}
.modal-head{padding:14px 20px;background:rgba(3,7,15,.6);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;}
.modal-title{font-family:var(--serif);font-size:17px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:10px}
.modal-close{width:32px;height:32px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface);color:var(--text2);cursor:pointer;display:grid;place-items:center;font-size:14px;transition:all .2s}
.modal-close:hover{background:var(--surface2);border-color:var(--border2);color:var(--text)}
.modal-body{padding:24px}
.emer-q-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}
@media(max-width:500px){.emer-q-grid{grid-template-columns:1fr}}
.emer-q-btn{padding:12px 14px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface);color:var(--text2);text-align:left;cursor:pointer;font-family:var(--sans);font-size:12.5px;font-weight:500;transition:all .2s;display:flex;align-items:flex-start;gap:10px;backdrop-filter:blur(8px);}
.emer-q-btn:hover{border-color:rgba(220,38,38,.3);background:rgba(220,38,38,.07);color:var(--text)}
.emer-q-ico{font-size:18px;flex-shrink:0;margin-top:1px}
.emer-q-text{line-height:1.4}
.emer-hotlines{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px;padding-top:16px;border-top:1px solid var(--border)}
.emer-hotline{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:4px;border:1px solid var(--border);background:var(--surface);text-decoration:none;color:var(--text2);font-family:var(--mono);font-size:10px;letter-spacing:.06em;transition:all .15s;}
.emer-hotline:hover{background:var(--surface2);border-color:var(--border2);color:var(--text)}

/* ── VOTING PLAN BUILDER PAGE ── */
#pg-plan{}
.plan-hero{padding:60px clamp(18px,6vw,80px) 40px;max-width:880px;margin:0 auto}
.plan-title{font-family:var(--serif);font-size:clamp(32px,4.5vw,56px);font-weight:700;color:var(--text);margin-bottom:12px}
.plan-sub{font-size:16px;color:var(--text2);line-height:1.65;max-width:560px;margin-bottom:40px}
.plan-steps{display:flex;flex-direction:column;gap:24px;max-width:680px;margin:0 auto}
.plan-step{border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);backdrop-filter:blur(16px);padding:22px 24px;position:relative;overflow:hidden;transition:border-color .25s;}
.plan-step:focus-within{border-color:rgba(220,38,38,.3)}
.ps-label{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--text3);margin-bottom:8px;display:flex;align-items:center;gap:8px}
.ps-num{width:18px;height:18px;border-radius:4px;background:rgba(220,38,38,.18);border:1px solid rgba(220,38,38,.3);color:var(--red3);display:grid;place-items:center;font-family:var(--mono);font-size:9px;font-weight:600;flex-shrink:0}
.ps-title{font-size:14px;font-weight:600;color:var(--text);margin-bottom:12px}
.ps-options{display:flex;flex-wrap:wrap;gap:8px}
.ps-opt{padding:5px 12px;border-radius:99px;border:1px solid var(--border);background:var(--surface);color:var(--text2);font-size:12px;font-weight:500;cursor:pointer;transition:all .2s;font-family:var(--sans);white-space:nowrap;}
.ps-opt:hover,.ps-opt.sel{border-color:rgba(220,38,38,.35);background:rgba(220,38,38,.1);color:var(--text)}
.ps-opt.sel{border-color:rgba(220,38,38,.45);font-weight:600}
.plan-generate-btn{width:100%;height:40px;border-radius:var(--radius-sm);border:none;background:var(--red2);color:#fff;font-family:var(--mono);font-size:10px;font-weight:500;letter-spacing:.1em;text-transform:uppercase;cursor:pointer;box-shadow:0 0 18px var(--red-glow);margin-top:12px;transition:all .2s;letter-spacing:.02em;
}
.plan-generate-btn:hover{filter:brightness(1.1);box-shadow:0 12px 36px rgba(220,38,38,.5);transform:translateY(-1px)}
/* Plan result */
.plan-result{
  max-width:680px;margin:32px auto 0;
  border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);backdrop-filter:blur(16px);padding:28px;display:none;}
.plan-result.show{display:block}
.pr-head{font-family:var(--serif);font-size:19px;font-weight:700;color:var(--text);margin-bottom:20px;display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid var(--border)}
.pr-section{margin-bottom:20px}
.pr-section-title{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--text3);margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
.pr-checklist{list-style:none;display:flex;flex-direction:column;gap:8px}
.pr-item{display:flex;align-items:flex-start;gap:10px;font-size:13px;line-height:1.6;color:var(--text2)}
.pr-check{width:16px;height:16px;border-radius:3px;border:1px solid var(--border);background:transparent;flex-shrink:0;cursor:pointer;display:grid;place-items:center;transition:all .2s;margin-top:2px;font-size:9px;font-family:var(--mono);color:transparent}
.pr-check.done{border-color:rgba(220,38,38,.5);background:rgba(220,38,38,.12);color:var(--red3)}
.pr-actions{display:flex;gap:10px;margin-top:20px;padding-top:20px;border-top:1px solid var(--border);flex-wrap:wrap}
.pr-btn{height:32px;padding:0 16px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface);color:var(--text2);font-family:var(--mono);font-size:10px;letter-spacing:.06em;cursor:pointer;transition:all .2s;}
.pr-btn:hover{background:var(--surface2);color:var(--text);border-color:var(--border2)}
.pr-btn.primary{background:rgba(220,38,38,.12);border-color:rgba(220,38,38,.35);color:var(--red3)}
.pr-btn.primary:hover{background:rgba(220,38,38,.18);border-color:rgba(220,38,38,.55)}

/* ── DEMOCRACY TIMELINE PAGE ── */
#pg-timeline{}
.tl-hero{text-align:center;padding:70px clamp(18px,6vw,80px) 40px;position:relative}
.tl-title{font-family:var(--serif);font-size:clamp(36px,5vw,68px);font-weight:700;color:var(--text);margin-bottom:14px}
.tl-sub{font-size:16px;color:var(--text2);max-width:540px;margin:0 auto 40px;line-height:1.65}
.tl-scroll-hint{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--text3);animation:bob 2.5s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(6px)}}
.tl-track{
  position:relative;max-width:900px;margin:0 auto;
  padding:0 clamp(18px,6vw,80px) 80px;
}
.tl-track::before{
  content:"";position:absolute;left:50%;transform:translateX(-50%);
  top:0;bottom:0;width:2px;
  background:linear-gradient(to bottom,transparent,rgba(220,38,38,.5) 8%,rgba(245,158,11,.4) 50%,rgba(29,78,216,.5) 92%,transparent);
}
@media(max-width:640px){.tl-track::before{left:28px;transform:none}}
.tl-item{
  display:flex;gap:28px;margin-bottom:48px;align-items:flex-start;
  opacity:0;transform:translateY(32px);
  transition:opacity .7s ease,transform .7s ease;
}
.tl-item:nth-child(even){flex-direction:row-reverse}
@media(max-width:640px){.tl-item,.tl-item:nth-child(even){flex-direction:row;padding-left:60px}}
.tl-item.visible{opacity:1;transform:none}
.tl-dot{width:34px;height:34px;border-radius:50%;flex-shrink:0;display:grid;place-items:center;font-size:14px;position:relative;z-index:2;margin-top:8px;border:1px solid;}
.tl-card{flex:1;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);backdrop-filter:blur(16px);padding:22px 24px;position:relative;overflow:hidden;transition:border-color .25s,box-shadow .25s;}
.tl-card:hover{border-color:var(--border2);box-shadow:0 16px 48px rgba(0,0,0,.3)}
.tl-year{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--text3);margin-bottom:8px}
.tl-event{font-family:var(--serif);font-size:16px;font-weight:700;color:var(--text);margin-bottom:8px;line-height:1.2}
.tl-desc{font-size:13.5px;color:var(--text2);line-height:1.65}
.tl-quote{font-style:italic;color:var(--gold2);border-left:1px solid rgba(245,158,11,.4);padding-left:14px;margin-top:12px;font-size:12.5px;line-height:1.65;opacity:.9;}
.tl-ending{
  text-align:center;padding:60px 20px;
  border-top:1px solid var(--border);margin-top:20px;
}
.tl-ending-title{font-family:var(--serif);font-size:clamp(26px,3.5vw,42px);font-weight:700;color:var(--text);margin-bottom:12px}
.tl-ending-sub{font-size:16px;color:var(--text2);max-width:480px;margin:0 auto 32px;line-height:1.65}

/* ── CIVIC ACHIEVEMENT BADGES PAGE ── */
#pg-badges{}
.badges-hero{padding:60px clamp(18px,6vw,80px) 40px;text-align:center}
.badges-title{font-family:var(--serif);font-size:clamp(32px,4.5vw,56px);font-weight:700;color:var(--text);margin-bottom:12px}
.badges-sub{font-size:15px;color:var(--text2);max-width:520px;margin:0 auto 48px;line-height:1.65}
.badges-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
  gap:16px;max-width:1000px;margin:0 auto;
  padding:0 clamp(18px,6vw,80px) 80px;
}
.badge-card{
  border:1px solid var(--border);border-radius:var(--radius);
  background:var(--surface);backdrop-filter:blur(12px);
  padding:24px;text-align:center;cursor:pointer;
  transition:all .25s;
  opacity:0;transform:translateY(20px);
}
.badge-card.visible{opacity:1;transform:none}
.badge-card:nth-child(2){transition-delay:.08s}
.badge-card:nth-child(3){transition-delay:.16s}
.badge-card:nth-child(4){transition-delay:.24s}
.badge-card:nth-child(5){transition-delay:.32s}
.badge-card:nth-child(6){transition-delay:.4s}
.badge-card:nth-child(7){transition-delay:.48s}
.badge-card:nth-child(8){transition-delay:.56s}
.badge-card.earned{border-color:rgba(245,158,11,.45);background:rgba(245,158,11,.07)}
.badge-card.earned:hover{box-shadow:0 16px 44px rgba(245,158,11,.15);transform:translateY(-3px)}
.badge-card:not(.earned){filter:grayscale(0.7);opacity:.6}
.badge-card:not(.earned):hover{filter:grayscale(.3);opacity:.85;border-color:var(--border2)}
.badge-icon{font-size:28px;margin-bottom:12px;display:block}
.badge-name{font-family:var(--serif);font-size:15px;font-weight:700;color:var(--text);margin-bottom:5px;line-height:1.2}
.badge-desc{font-size:12px;color:var(--text3);line-height:1.55;margin-bottom:10px}
.badge-status{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase}
.badge-earned-lbl{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--gold2)}
.badge-locked-lbl{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--text3)}
.badge-unlock-btn{margin-top:8px;padding:5px 10px;border-radius:99px;border:1px solid var(--border);background:var(--surface);color:var(--text2);font-size:11px;font-weight:500;cursor:pointer;transition:all .2s;font-family:var(--mono);letter-spacing:.06em;text-transform:uppercase;}
.badge-unlock-btn:hover{border-color:rgba(220,38,38,.35);background:rgba(220,38,38,.1);color:var(--text)}
.badges-progress{
  max-width:680px;margin:0 auto 32px;
  padding:0 clamp(18px,6vw,80px);
}
.bp-bar-wrap{height:3px;background:var(--border);border-radius:2px;overflow:hidden;margin-bottom:8px}
.bp-bar{height:100%;background:linear-gradient(to right,var(--red2),var(--gold2));border-radius:2px;transition:width 1.2s cubic-bezier(.22,1,.36,1)}
.bp-label{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;color:var(--text3);text-transform:uppercase}

/* ── TRUST / SECURITY SECTION (inline on home) ── */
.trust-section{
  padding:80px clamp(18px,6vw,80px);
  border-top:1px solid var(--border);
  position:relative;z-index:10;
}
.trust-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:32px}
.trust-card{
  border:1px solid var(--border);border-radius:var(--radius);
  background:var(--surface);backdrop-filter:blur(12px);
  padding:22px;transition:all .25s;
}
.trust-card:hover{border-color:var(--border2);box-shadow:0 16px 48px rgba(0,0,0,.3)}
.trust-icon{font-size:24px;margin-bottom:14px}
.trust-title{font-size:13px;font-weight:600;color:var(--text);margin-bottom:5px}
.trust-desc{font-size:12px;color:var(--text2);line-height:1.55}
.verified-badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:4px;background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.2);color:#4ade80;font-family:var(--mono);font-size:9px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;margin-top:10px;}

/* ── HOLOGRAM ORB ── */
.orb-wrapper{display:none}

/* Nav additions */
.nav-btn-new{
  padding:7px 14px;border-radius:var(--radius-sm);border:none;
  background:transparent;color:var(--text2);font-family:var(--sans);
  font-size:13px;font-weight:500;cursor:pointer;transition:all .2s;white-space:nowrap;
}
.nav-btn-new:hover,.nav-btn-new.active{color:var(--text);background:var(--surface2)}
.nav-btn-new.active{color:var(--gold2)}

/* Mobile drawer additions */
.mob-item-new{padding:12px 16px;border-radius:var(--radius-sm);font-size:15px;font-weight:500;color:var(--text2);cursor:pointer;border:none;background:none;text-align:left;font-family:var(--sans);transition:all .15s}
.mob-item-new:hover,.mob-item-new.active{color:var(--text);background:var(--surface)}
.mob-item-new.active{color:var(--gold2)}

/* Accurate SVG map rendering patch */
.bb-accurate-us-map{position:absolute;inset:0;width:100%;height:100%;display:block;overflow:visible}
.bb-state{transition:fill-opacity .16s ease, stroke-width .16s ease, filter .16s ease}
.bb-state:hover{filter:drop-shadow(0 8px 18px rgba(255,255,255,.12))}
#bg-map-tooltip.globe-tooltip{bottom:auto;left:0;top:0;transform:none;min-width:220px;max-width:320px;text-align:left}
.globe-3d-wrap{min-height:360px}
@media(max-width:700px){.globe-3d-wrap{min-height:300px}.map-stage{height:420px!important}.bb-accurate-us-map text{font-size:9px}}



/* ═══════════════════════════════════════════
   BALLotBuddy 3D POLISH LAYER — SAFE ADDITIVE ONLY
   Keeps verified chatbot/data logic untouched.
   ═══════════════════════════════════════════ */
:root{
  --bb-depth-shadow:0 22px 70px rgba(0,0,0,.38),0 0 42px rgba(220,38,38,.08);
  --bb-depth-border:rgba(255,255,255,.16);
  --bb-perspective:1200px;
}
body::before{
  content:"";position:fixed;inset:0;z-index:2;pointer-events:none;opacity:.22;
  background:
    linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px),
    linear-gradient(0deg,rgba(255,255,255,.025) 1px,transparent 1px);
  background-size:72px 72px;
  mask-image:radial-gradient(circle at 50% 30%,black 0%,transparent 75%);
  transform:translateZ(0);
}
[data-theme="light"] body::before{opacity:.16;background:
  linear-gradient(90deg,rgba(13,21,38,.045) 1px,transparent 1px),
  linear-gradient(0deg,rgba(13,21,38,.035) 1px,transparent 1px);
}
.bb-3d-ambient{position:fixed;inset:0;z-index:3;pointer-events:none;overflow:hidden;perspective:1200px}
.bb-3d-orb{
  position:absolute;width:220px;height:220px;border-radius:50%;opacity:.42;
  background:radial-gradient(circle at 30% 30%,rgba(245,158,11,.22),rgba(220,38,38,.12) 42%,transparent 68%);
  filter:blur(.2px);transform-style:preserve-3d;animation:bbFloat3D 14s ease-in-out infinite;
}
.bb-3d-orb.o1{right:7vw;top:18vh}.bb-3d-orb.o2{left:6vw;top:66vh;width:150px;height:150px;animation-delay:-5s;background:radial-gradient(circle at 30% 30%,rgba(96,165,250,.18),rgba(29,78,216,.10) 42%,transparent 70%)}
.bb-3d-wire{
  position:absolute;width:340px;height:340px;border-radius:28px;border:1px solid rgba(245,240,232,.10);
  transform:rotateX(62deg) rotateZ(35deg);right:8vw;bottom:10vh;opacity:.45;animation:bbWireSpin 22s linear infinite;
  box-shadow:0 0 40px rgba(245,158,11,.06),inset 0 0 42px rgba(29,78,216,.05)
}
.bb-3d-wire::before,.bb-3d-wire::after{content:"";position:absolute;inset:34px;border:1px solid rgba(245,240,232,.075);border-radius:22px}.bb-3d-wire::after{inset:74px;border-color:rgba(220,38,38,.12)}
@keyframes bbFloat3D{0%,100%{transform:translate3d(0,0,0) rotateX(0deg) rotateY(0deg)}50%{transform:translate3d(18px,-28px,60px) rotateX(18deg) rotateY(-26deg)}}
@keyframes bbWireSpin{to{transform:rotateX(62deg) rotateZ(395deg)}}
.hero{perspective:var(--bb-perspective)}
.hero-inner{transform-style:preserve-3d}.hero-h1{transform:translateZ(14px)}.hero-tag,.hero-desc{transform:translateZ(8px)}
.p-box,.info-card,.q-card,.about-card,.plan-step,.tl-card,.badge-card,.state-card,.map-stage,.modal-box{
  transform-style:preserve-3d;will-change:transform,box-shadow,border-color;backface-visibility:hidden;
}
.bb-tilt-ready{transition:transform .28s ease,border-color .25s ease,box-shadow .25s ease!important}
.bb-tilt-ready:hover{box-shadow:var(--bb-depth-shadow);border-color:var(--bb-depth-border)}
.info-card::after,.q-card::before,.about-card::after,.plan-step::after,.tl-card::after,.badge-card::after{
  content:"";position:absolute;inset:0;pointer-events:none;opacity:0;transition:opacity .25s ease;
  background:linear-gradient(120deg,transparent 0%,rgba(255,255,255,.10) 38%,transparent 62%);
  transform:translateX(-80%) skewX(-18deg);
}
.info-card:hover::after,.q-card:hover::before,.about-card:hover::after,.plan-step:hover::after,.tl-card:hover::after,.badge-card:hover::after{opacity:.55;animation:bbSheen 1.1s ease both}
@keyframes bbSheen{to{transform:translateX(120%) skewX(-18deg)}}
.map-stage{perspective:1200px;background:linear-gradient(145deg,rgba(3,10,28,.88),rgba(8,17,38,.72))!important;border-color:var(--border)!important;box-shadow:0 34px 110px rgba(0,0,0,.58),0 0 0 1px rgba(255,255,255,.04),inset 0 1px 0 rgba(255,255,255,.07)!important}
[data-theme="light"] .map-stage{background:linear-gradient(145deg,rgba(255,255,255,.86),rgba(220,230,255,.62))!important;box-shadow:0 24px 80px rgba(13,21,38,.15),inset 0 1px 0 rgba(255,255,255,.85)!important}
.map-stage::before{content:"";position:absolute;inset:18px;border-radius:16px;pointer-events:none;z-index:1;border:1px solid rgba(245,158,11,.10);box-shadow:inset 0 0 42px rgba(245,158,11,.035),0 0 30px rgba(29,78,216,.05)}
.map-stage::after{content:"";position:absolute;left:50%;top:50%;width:72%;height:72%;transform:translate(-50%,-50%) rotateX(68deg);border-radius:50%;pointer-events:none;z-index:1;border:1px dashed rgba(96,165,250,.16);opacity:.65;animation:bbMapHalo 18s linear infinite}
@keyframes bbMapHalo{to{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(360deg)}}
#map-canvas{z-index:2}.map-stage .bb-map-depth-label{position:absolute;right:18px;top:16px;z-index:4;font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--text3);padding:6px 9px;border:1px solid var(--border);border-radius:6px;background:rgba(5,12,30,.5);backdrop-filter:blur(10px)}
[data-theme="light"] .map-stage .bb-map-depth-label{background:rgba(255,255,255,.55)}
.globe-wrap,.globe-3d-wrap{filter:drop-shadow(0 24px 45px rgba(0,0,0,.38)) drop-shadow(0 0 34px rgba(220,38,38,.12));transform-style:preserve-3d}
.globe-wrap::after,.globe-3d-wrap::after{content:"";position:absolute;inset:10%;border-radius:50%;border:1px solid rgba(245,158,11,.12);pointer-events:none;transform:rotateX(67deg);box-shadow:0 0 36px rgba(245,158,11,.08);animation:bbGlobeOrbit 16s linear infinite}
@keyframes bbGlobeOrbit{to{transform:rotateX(67deg) rotateZ(360deg)}}
.nav-badge{transform-style:preserve-3d;animation:badge-pulse 3s ease-in-out infinite,bbBadgeTilt 7s ease-in-out infinite!important}
@keyframes bbBadgeTilt{0%,100%{transform:rotateX(0) rotateY(0)}50%{transform:rotateX(12deg) rotateY(-14deg)}}
.bb-hero-console{margin-top:18px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;transform:translateZ(12px);animation:fi .9s ease 1.05s both}
.bb-console-chip{display:inline-flex;align-items:center;gap:7px;height:28px;padding:0 10px;border:1px solid var(--border);border-radius:6px;background:rgba(255,255,255,.035);font-family:var(--mono);font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--text3);backdrop-filter:blur(12px)}
.bb-console-dot{width:6px;height:6px;border-radius:50%;background:var(--gold2);box-shadow:0 0 10px var(--gold2);animation:bbDotPulse 2.4s ease-in-out infinite}.bb-console-chip:nth-child(2) .bb-console-dot{background:var(--blue3);box-shadow:0 0 10px var(--blue3);animation-delay:.4s}.bb-console-chip:nth-child(3) .bb-console-dot{background:var(--red3);box-shadow:0 0 10px var(--red3);animation-delay:.8s}
@keyframes bbDotPulse{0%,100%{opacity:.45;transform:scale(.82)}50%{opacity:1;transform:scale(1.18)}}
@media(max-width:768px){.bb-3d-orb,.bb-3d-wire{opacity:.22}.bb-hero-console{display:none}.map-stage::after{display:none}}
@media(prefers-reduced-motion:reduce){.bb-3d-orb,.bb-3d-wire,.map-stage::after,.globe-wrap::after,.globe-3d-wrap::after,.nav-badge,.bb-console-dot{animation:none!important}.bb-tilt-ready{transform:none!important}}



/* ──────────────────────────────────────────────
   FINAL POLISH PATCH — light mode, maps, globe, questions, no badges
   ────────────────────────────────────────────── */
#nb-badges,#md-badges,#pg-badges{display:none!important}
.nav-links{gap:8px}

/* Hero line cleanup: exact clean stacked slogan */
.hero-h1{letter-spacing:-.035em;max-width:720px}
.hero-h1 span{display:block;line-height:.88;margin:0 0 .08em 0;white-space:nowrap}
.h1-l1::after,.h1-l2::after,.h1-l3::after{content:"."}
.h1-l3{color:var(--blue2)!important;-webkit-text-stroke:0!important;text-shadow:0 0 42px rgba(29,78,216,.42)}
[data-theme="light"] .h1-l3{color:#1d4ed8!important;text-shadow:0 0 26px rgba(29,78,216,.18)}

/* More accurate interactive globe surface */
.globe-wrap{pointer-events:auto!important;overflow:visible!important;width:min(660px,48vw)!important;height:min(660px,48vw)!important;right:clamp(-80px,-4vw,20px)!important}
.globe-wrap::after,.globe-3d-wrap::after,.map-stage::after{display:none!important}
.bb-orthographic-globe{width:100%;height:100%;display:block;cursor:grab;filter:drop-shadow(0 28px 54px rgba(0,0,0,.45)) drop-shadow(0 0 46px rgba(29,78,216,.22))}
.bb-orthographic-globe:active{cursor:grabbing}
.bb-us-glow{filter:drop-shadow(0 0 9px rgba(245,158,11,.95)) drop-shadow(0 0 22px rgba(245,158,11,.75))}

/* Light mode should feel premium, not washed out */
[data-theme="light"]{
  --bg:#f6f9ff;--bg2:#eef4ff;--bg3:#e7eefc;
  --surface:rgba(255,255,255,.78);--surface2:rgba(255,255,255,.96);
  --border:rgba(15,23,42,.11);--border2:rgba(15,23,42,.18);
  --text:#0b1224;--text2:rgba(15,23,42,.68);--text3:rgba(15,23,42,.46);
}
[data-theme="light"] body{background:radial-gradient(circle at 78% 12%,rgba(220,38,38,.06),transparent 28%),radial-gradient(circle at 20% 18%,rgba(29,78,216,.08),transparent 32%),linear-gradient(180deg,#f8fbff 0%,#edf4ff 100%)}
[data-theme="light"] #bg-canvas-wrap{opacity:.22}
[data-theme="light"] .bg-overlay{background:radial-gradient(ellipse 75% 60% at 50% 30%,transparent 0%,rgba(246,249,255,.45) 56%,rgba(246,249,255,.95) 100%)}
[data-theme="light"] .hero{background:linear-gradient(180deg,rgba(255,255,255,.72),rgba(246,249,255,.25) 62%,transparent)}
[data-theme="light"] .hero-tag{background:rgba(255,255,255,.8);box-shadow:0 10px 30px rgba(15,23,42,.06)}
[data-theme="light"] .p-box,[data-theme="light"] .info-card,[data-theme="light"] .about-card,[data-theme="light"] .plan-step,[data-theme="light"] .tl-card,[data-theme="light"] .state-card{background:rgba(255,255,255,.82)!important;border-color:rgba(15,23,42,.12)!important;box-shadow:0 18px 50px rgba(15,23,42,.07)!important}

/* Neater Common Questions section */
.q-section{padding:56px clamp(18px,5vw,72px) 70px;margin:0 clamp(10px,1.5vw,24px) 70px;border:1px solid var(--border);border-radius:28px;background:linear-gradient(145deg,rgba(255,255,255,.055),rgba(255,255,255,.025));box-shadow:0 28px 90px rgba(0,0,0,.25);backdrop-filter:blur(18px)}
[data-theme="light"] .q-section{background:rgba(255,255,255,.86);border-color:rgba(15,23,42,.10);box-shadow:0 28px 80px rgba(15,23,42,.09)}
.q-section .section-tag{margin-bottom:24px;color:var(--text2)}
.cards-grid{display:grid!important;grid-template-columns:repeat(5,minmax(180px,1fr))!important;gap:18px!important;align-items:stretch}
.q-card{min-height:176px;padding:24px 24px 22px!important;border-radius:18px!important;background:linear-gradient(145deg,rgba(255,255,255,.07),rgba(255,255,255,.035))!important;border:1px solid var(--border)!important;box-shadow:0 16px 42px rgba(0,0,0,.18)!important}
[data-theme="light"] .q-card{background:linear-gradient(145deg,#ffffff,#f8fbff)!important;border-color:rgba(15,23,42,.12)!important;box-shadow:0 16px 42px rgba(15,23,42,.08)!important}
.qc-icon{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;margin-bottom:20px!important;background:rgba(29,78,216,.10);font-size:22px!important}
.q-card:nth-child(2) .qc-icon{background:rgba(220,38,38,.10)}
.q-card:nth-child(3) .qc-icon{background:rgba(22,163,74,.10)}
.q-card:nth-child(4) .qc-icon{background:rgba(124,58,237,.10)}
.q-card:nth-child(5) .qc-icon{background:rgba(245,158,11,.12)}
.q-card:nth-child(6) .qc-icon{background:rgba(34,197,94,.12)}
.qc-title{font-size:16px!important;letter-spacing:-.01em;margin-bottom:7px!important}
.qc-desc{font-size:13px!important;color:var(--text2)!important}
.qc-cta{color:var(--red2)!important;margin-top:20px!important;font-weight:700}
@media(max-width:1100px){.cards-grid{grid-template-columns:repeat(3,minmax(180px,1fr))!important}}
@media(max-width:700px){.cards-grid{grid-template-columns:1fr!important}.q-section{margin:0 12px 44px;padding:32px 18px}.hero-h1 span{white-space:normal}}

/* Make maps gorgeous and remove the floating oval/halo artifact */
.map-section{background:linear-gradient(180deg,transparent,rgba(29,78,216,.035),transparent)}
.map-stage{overflow:hidden!important;border-radius:28px!important;background:radial-gradient(circle at 48% 44%,rgba(29,78,216,.18),transparent 46%),linear-gradient(145deg,rgba(5,12,30,.96),rgba(11,21,44,.88))!important;box-shadow:0 34px 105px rgba(0,0,0,.52),inset 0 1px 0 rgba(255,255,255,.09)!important}
[data-theme="light"] .map-stage{background:radial-gradient(circle at 45% 42%,rgba(29,78,216,.13),transparent 46%),linear-gradient(145deg,#f9fbff,#dce7f7)!important;border-color:rgba(15,23,42,.12)!important;box-shadow:0 28px 90px rgba(15,23,42,.14),inset 0 1px 0 rgba(255,255,255,.9)!important}
#map-tooltip{max-width:310px!important;min-width:250px!important;border-radius:16px!important;background:rgba(5,12,30,.94)!important;box-shadow:0 22px 60px rgba(0,0,0,.45)!important}
[data-theme="light"] #map-tooltip{background:rgba(255,255,255,.96)!important;box-shadow:0 22px 60px rgba(15,23,42,.16)!important;color:#0b1224!important}
.state-locator-panel{border-radius:22px!important}
[data-theme="light"] .state-locator-panel{background:rgba(255,255,255,.88)!important;border-color:rgba(15,23,42,.11)!important;box-shadow:0 24px 70px rgba(15,23,42,.10)!important}
.globe-section{padding-top:40px!important}
.globe-3d-wrap{border:1px solid var(--border);border-radius:28px;background:radial-gradient(circle at 48% 45%,rgba(29,78,216,.18),transparent 48%),linear-gradient(145deg,rgba(5,12,30,.9),rgba(11,21,44,.72));box-shadow:0 26px 76px rgba(0,0,0,.32);overflow:hidden}
[data-theme="light"] .globe-3d-wrap{background:radial-gradient(circle at 48% 45%,rgba(29,78,216,.13),transparent 48%),linear-gradient(145deg,#ffffff,#dce7f7);box-shadow:0 22px 70px rgba(15,23,42,.12)}
#bg-map-canvas{border-radius:28px!important}

/* remove old badges from any generated arrays/active buttons */
.badges-hero,.badges-grid,.badges-progress{display:none!important}


/* ──────────────────────────────────────────────
   TRUE FINAL HOTFIX — light-mode battleground overlay readability
   fixes invisible text inside the priority-state hover/tooltip area
   ────────────────────────────────────────────── */
[data-theme="light"] .globe-section{
  background:linear-gradient(180deg,#f8fbff 0%,#edf4ff 48%,#f8fbff 100%)!important;
}
[data-theme="light"] .globe-info,
[data-theme="light"] .globe-info *:not(.dot):not(.sc-dot){
  color:#0b1224!important;
}
[data-theme="light"] .globe-sub,
[data-theme="light"] .section-tag,
[data-theme="light"] .sc-ev{
  color:rgba(15,23,42,.68)!important;
}
[data-theme="light"] .globe-3d-wrap{
  background:linear-gradient(145deg,#ffffff 0%,#eaf1ff 58%,#dbe6f7 100%)!important;
  border:1px solid rgba(15,23,42,.12)!important;
  box-shadow:0 28px 80px rgba(15,23,42,.13), inset 0 1px 0 rgba(255,255,255,.95)!important;
}
[data-theme="light"] .bb-accurate-us-map rect{
  fill:rgba(255,255,255,.28)!important;
}
[data-theme="light"] .bb-accurate-us-map text{
  fill:#0b1224!important;
  stroke:rgba(255,255,255,.94)!important;
  stroke-width:3.25px!important;
  paint-order:stroke!important;
}
[data-theme="light"] .bb-state{
  stroke:rgba(255,255,255,.90)!important;
}
[data-theme="light"] #bg-map-tooltip.globe-tooltip{
  background:rgba(255,255,255,.97)!important;
  border:1px solid rgba(15,23,42,.16)!important;
  box-shadow:0 24px 70px rgba(15,23,42,.18)!important;
  color:#0b1224!important;
  opacity:0;
}
[data-theme="light"] #bg-map-tooltip.globe-tooltip.show{opacity:1!important}
[data-theme="light"] #bg-map-tooltip .tt-state{color:#0b1224!important}
[data-theme="light"] #bg-map-tooltip .tt-abbr,
[data-theme="light"] #bg-map-tooltip .tt-row{color:rgba(15,23,42,.68)!important}
[data-theme="light"] #bg-map-tooltip .tt-val{color:#0b1224!important}
[data-theme="light"] #bg-map-tooltip .tt-cta{
  color:#dc2626!important;
  border-top-color:rgba(15,23,42,.12)!important;
}
[data-theme="light"] .state-card{
  background:rgba(255,255,255,.92)!important;
  border-color:rgba(15,23,42,.12)!important;
}
[data-theme="light"] .state-card .sc-name{color:#0b1224!important}
[data-theme="light"] .state-card .sc-ev{color:rgba(15,23,42,.58)!important}
[data-theme="light"] .state-card .sc-status.sc-t-swing{color:#b45309!important}
[data-theme="light"] .state-card .sc-status.sc-t-lean-r{color:#dc2626!important}
[data-theme="light"] .state-card .sc-status.sc-t-lean-b{color:#2563eb!important}
[data-theme="light"] .legend .leg-chip{background:rgba(255,255,255,.72)!important}
[data-theme="light"] .leg-swing{color:#b45309!important;border-color:rgba(217,119,6,.32)!important}
[data-theme="light"] .leg-r{color:#dc2626!important;border-color:rgba(220,38,38,.26)!important}
[data-theme="light"] .leg-b{color:#2563eb!important;border-color:rgba(37,99,235,.28)!important}

</style>
</head>
<body>

<!-- ═══ EMERGENCY FLOATING BUTTON + ORB ═══ -->
<button class="emer-fab" onclick="openEmer()">
  <span class="emer-fab-ico">⚠</span><span>Voting Rights Help</span>
</button>

<!-- Civic guide accessible via Ask a Question navigation -->

<!-- ═══ EMERGENCY MODAL ═══ -->
<div id="emer-modal" class="modal-backdrop" onclick="closeEmerOutside(event)">
  <div class="modal-box">
    <div class="modal-head">
      <div class="modal-title"><div class="vl-icon" style="width:18px;height:18px;font-size:8px">VL</div>Voting Rights Assistance</div>
      <button class="modal-close" onclick="closeEmer()">✕</button>
    </div>
    <div class="modal-body">
      <p style="font-size:14px;color:var(--text2);margin-bottom:18px;line-height:1.6">
        Are you at the polls right now? Select your situation and VoterLens will give you step-by-step guidance and your legal rights — instantly.
      </p>
      <div class="emer-q-grid">
        <button class="emer-q-btn" onclick="emerAsk('I am being told I cannot vote. What are my rights?')"><div class="emer-q-ico">🚫</div><div class="emer-q-text">I'm being told I can't vote</div></button>
        <button class="emer-q-btn" onclick="emerAsk('My name is not on the voter list. What should I do?')"><div class="emer-q-ico">📋</div><div class="emer-q-text">My name is not on the voter list</div></button>
        <button class="emer-q-btn" onclick="emerAsk('I forgot my voter ID. Can I still vote?')"><div class="emer-q-ico">🪪</div><div class="emer-q-text">I forgot my ID</div></button>
        <button class="emer-q-btn" onclick="emerAsk('Someone is intimidating or harassing voters at my polling place. What do I do?')"><div class="emer-q-ico">⚠️</div><div class="emer-q-text">Voter intimidation happening</div></button>
        <button class="emer-q-btn" onclick="emerAsk('The voting machine is not working. What should I do?')"><div class="emer-q-ico">🖥️</div><div class="emer-q-text">Voting machine not working</div></button>
        <button class="emer-q-btn" onclick="emerAsk('My polling place is closed or I was turned away while in line. What are my rights?')"><div class="emer-q-ico">🏛️</div><div class="emer-q-text">Polling place closed / turned away in line</div></button>
        <button class="emer-q-btn" onclick="emerAsk('I need a provisional ballot. How do I get one and will it count?')"><div class="emer-q-ico">📝</div><div class="emer-q-text">I need a provisional ballot</div></button>
        <button class="emer-q-btn" onclick="emerAsk('I moved recently. Can I still vote? How?')"><div class="emer-q-ico">🏠</div><div class="emer-q-text">I moved — can I still vote?</div></button>
      </div>
      <div class="emer-hotlines">
        <a class="emer-hotline" href="tel:18668687683" target="_blank">📞 866-OUR-VOTE (nonpartisan)</a>
        <a class="emer-hotline" href="tel:18883626837" target="_blank">📞 888-Ve-Y-Vota (Spanish)</a>
        <a class="emer-hotline" href="https://www.eac.gov/voters" target="_blank">🌐 EAC Voter Help</a>
      </div>
    </div>
  </div>
</div>

<div id="bg-canvas-wrap">
  <canvas id="bg-canvas"></canvas>
  <div class="bg-overlay"></div>
</div>

<nav>
  <div class="nav-logo" onclick="goPage('home')">
    <div class="nav-badge">&#9733;</div>
    VoterLens
  </div>
  <div class="nav-links">
    <button class="nav-btn active" id="nb-home" onclick="goPage('home')">Home</button>
    <button class="nav-btn" id="nb-chat" onclick="goPage('chat')">Ask a Question</button>
    <button class="nav-btn-new" id="nb-plan" onclick="goPage('plan')">Voting Plan</button>
    <button class="nav-btn-new" id="nb-timeline" onclick="goPage('timeline')">History</button>
  </div>
  <div class="nav-actions">
    <button class="theme-toggle" id="theme-btn" onclick="toggleTheme()" title="Toggle light/dark">&#127769;</button>
    <button class="nav-cta" onclick="goPage('chat')">Get Voting Info &#8594;</button>
    <button class="ham" id="ham" onclick="toggleDrw()" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
  </div>
</nav>
<div id="mob-drawer" class="mob-drawer">
  <button class="mob-item active" id="md-home" onclick="goPage('home');toggleDrw()">&#127968; Home</button>
  <button class="mob-item" id="md-chat" onclick="goPage('chat');toggleDrw()">&#128172; Ask a Question</button>
  <button class="mob-item-new" id="md-plan" onclick="goPage('plan');toggleDrw()">📋 Voting Plan Builder</button>
  <button class="mob-item-new" id="md-timeline" onclick="goPage('timeline');toggleDrw()">📜 Democracy Timeline</button>
</div>
<div class="flag-bar"><div class="fb-r"></div><div class="fb-w"></div><div class="fb-b"></div></div>

<!-- ══ HOME ══ -->
<div id="pg-home" class="page active">
  <div class="hero">
    <div class="flag-deco">
      <div class="f-stripe" style="top:0%"></div><div class="f-stripe" style="top:7.69%"></div>
      <div class="f-stripe" style="top:15.38%"></div><div class="f-stripe" style="top:23.07%"></div>
      <div class="f-stripe" style="top:30.76%"></div><div class="f-stripe" style="top:38.45%"></div>
      <div class="f-stripe" style="top:46.14%"></div><div class="f-stripe" style="top:53.83%"></div>
      <div class="f-stripe" style="top:61.52%"></div><div class="f-stripe" style="top:69.21%"></div>
      <div class="f-stripe" style="top:76.9%"></div><div class="f-stripe" style="top:84.59%"></div>
      <div class="f-stripe" style="top:92.28%"></div>
    </div>
    <div class="hero-inner">
      <div class="hero-tag"><div class="tag-star"></div>Nonpartisan &middot; Official Sources &middot; All 50 States</div>
      <h1 class="hero-h1">
        <span class="h1-l1">YOUR VOTE</span>
        <span class="h1-l2">YOUR VOICE</span>
        <span class="h1-l3">YOUR RIGHT</span>
      </h1>
      <p class="hero-desc">AI-powered voting guidance for every American.<br/><strong>Registration. ID requirements. Polling hours. Mail-in ballots. Nearby polling places.</strong><br/>Every answer points users back to official government sources &mdash; never partisan.</p>
      <div class="prompt-wrap">
        <div class="p-box">
          <textarea class="p-ta" id="home-ta" placeholder="Ask anything about voting in your state &mdash; registration deadlines, ID rules, polling hours, mail-in ballots, checking your registration status..." rows="3"></textarea>
          <div class="p-bot">
            <select class="p-state" id="home-state"></select>
            <div class="p-hints">
              <span class="p-hint" onclick="hint('How do I register to vote?')">&#128203; Register</span>
              <span class="p-hint" onclick="hint('What ID do I need to vote?')">&#129306; Voter ID</span>
              <span class="p-hint" onclick="hint('How do I get a mail-in ballot?')">&#9993; Mail-in</span>
              <span class="p-hint" onclick="hint('When is early voting?')">&#128197; Early</span>
              <span class="p-hint" onclick="hint('Where is my polling place?')">&#128506; Polls</span>
            </div>
            <button class="p-send" onclick="homeSubmit()">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </div>
      </div>
      <div class="hero-stats">
        <div><div class="stat-n">50</div><div class="stat-l">States</div></div>
        <div><div class="stat-n">100%</div><div class="stat-l">Gov. Sources</div></div>
        <div><div class="stat-n">0</div><div class="stat-l">Bias</div></div>
        <div><div class="stat-n">Free</div><div class="stat-l">Always</div></div>
      </div>
    </div>
    <div class="globe-wrap"><canvas id="globe-c" style="width:100%;height:100%;display:block"></canvas></div>
  </div>


    <!-- ── INTERACTIVE USA MAP ── -->
  <section class="map-section" id="map-section">
    <div class="map-header">
      <div class="section-tag" style="justify-content:center">Interactive 50-State Map</div>
      <div class="map-title">Touch a State. Open Official Voting Help.</div>
      <p class="map-sub">Hover or tap any state to expand trusted options for polling-place lookup, local election-office mailing addresses, mail ballots, and registration through official government websites.</p>
    </div>
    <div class="map-stage" style="height:clamp(420px,50vw,580px)">
      <canvas id="map-canvas" style="position:absolute;top:0;left:0;width:100%;height:100%"></canvas>
      <div id="map-tooltip"></div>
    </div>
    <div class="map-legend">
      <div class="ml-item"><div class="ml-dot ml-r"></div>Category A</div>
      <div class="ml-item"><div class="ml-dot ml-swing"></div>Priority Review</div>
      <div class="ml-item"><div class="ml-dot ml-b"></div>Category B</div>
      <div class="ml-item"><div class="ml-dot" style="background:rgba(186,230,253,.8)"></div>Hover to explore</div>
    </div>
    <div class="map-controls">
      <button class="mc-btn" id="mc-rotate" onclick="window.mapToggleRotate&&mapToggleRotate()">&#9696; Auto&#8209;Rotate</button>
      <button class="mc-btn" onclick="window.mapReset&&mapReset()">&#8635; Reset View</button>
      <span class="mc-hint">Drag to rotate &middot; Scroll to zoom &middot; Click any state for voting info</span>
    </div>
    <div id="state-locator-panel" class="state-locator-panel" aria-live="polite">
      <div class="locator-empty">
        <div class="locator-kicker">50-State Voting Guide</div>
        <h3>Click any state on the map</h3>
        <p>VoterLens will show official government resources for voter registration, ID requirements, and election deadlines — specific to that state.</p>
      </div>
    </div>
  </section>


  <!-- SCROLL INFOGRAPHICS -->
  <div class="info-section" id="infographics">
    <div class="section-tag">Voting in America</div>
    <div class="section-title">Your vote is powerful. Here&rsquo;s the data.</div>
    <div class="infogrid">
      <div class="info-card" style="--card-glow:linear-gradient(135deg,rgba(220,38,38,.08),transparent)">
        <div class="ic-icon">&#128203;</div>
        <div class="ic-num">159M</div>
        <div class="ic-label">Registered Voters</div>
        <div class="ic-desc">More Americans are registered to vote today than ever before in history.</div>
        <div class="ic-bar"><div class="ic-fill" style="--pct:88%"></div></div>
      </div>
      <div class="info-card" style="--card-glow:linear-gradient(135deg,rgba(29,78,216,.08),transparent)">
        <div class="ic-icon">&#128442;</div>
        <div class="ic-num">66%</div>
        <div class="ic-label">2020 Voter Turnout</div>
        <div class="ic-desc">The highest presidential election turnout in over 120 years.</div>
        <div class="ic-bar"><div class="ic-fill" style="--pct:66%"></div></div>
      </div>
      <div class="info-card" style="--card-glow:linear-gradient(135deg,rgba(245,158,11,.07),transparent)">
        <div class="ic-icon">&#9993;</div>
        <div class="ic-num">46%</div>
        <div class="ic-label">Voted by Mail in 2020</div>
        <div class="ic-desc">Nearly half of all votes were cast by mail or early in-person in 2020.</div>
        <div class="ic-bar"><div class="ic-fill" style="--pct:46%"></div></div>
      </div>
      <div class="info-card" style="--card-glow:linear-gradient(135deg,rgba(96,165,250,.08),transparent)">
        <div class="ic-icon">&#127818;</div>
        <div class="ic-num">50</div>
        <div class="ic-label">Different State Rules</div>
        <div class="ic-desc">Every state sets its own voting laws. VoterLens knows them all.</div>
        <div class="ic-bar"><div class="ic-fill" style="--pct:100%"></div></div>
      </div>
    </div>
  </div>

  <!-- QUICK QUESTION CARDS -->
  <div class="q-section">
    <div class="section-tag">Common Questions</div>
    <div class="cards-grid" id="cards-grid"></div>
  </div>

  <!-- ── TRUST / CYBERSECURITY SECTION ── -->
  <section class="trust-section">
    <div class="section-tag" style="justify-content:flex-start">Verified &amp; Trustworthy</div>
    <div class="section-title" style="font-size:clamp(26px,3.5vw,42px);margin-bottom:0">How We Keep You Informed — Not Misled</div>
    <div class="trust-grid">
      <div class="trust-card">
        <div class="trust-icon">🛡️</div>
        <div class="trust-title">Official Sources Only</div>
        <div class="trust-desc">Every answer VoterLens gives cites official government websites — Secretary of State offices, Vote.gov, EAC, and USA.gov. Never blogs, social media, or partisan sites.</div>
        <div class="verified-badge">✓ Gov-Verified</div>
      </div>
      <div class="trust-card">
        <div class="trust-icon">🤖</div>
        <div class="trust-title">AI + Official Data</div>
        <div class="trust-desc">Powered by Claude AI (Anthropic), trained to cite only authoritative government sources. Every response includes direct links so you can verify everything yourself.</div>
        <div class="verified-badge">✓ Source-Cited</div>
      </div>
      <div class="trust-card">
        <div class="trust-icon">🔒</div>
        <div class="trust-title">Privacy First</div>
        <div class="trust-desc">VoterLens never stores your personal information, voter registration details, or location data. No accounts required. No tracking. No data sold — ever.</div>
        <div class="verified-badge">✓ No Data Stored</div>
      </div>
      <div class="trust-card">
        <div class="trust-icon">⚖️</div>
        <div class="trust-title">100% Nonpartisan</div>
        <div class="trust-desc">VoterLens never tells you who to vote for. Our mission is to inform, not influence. Voting rights belong to every American, regardless of party.</div>
        <div class="verified-badge">✓ Nonpartisan</div>
      </div>
    </div>
  </section>

</div>

<!-- ══ CHAT ══ -->
<div id="pg-chat" class="page">
  <div class="chat-side">
    <div class="side-sw"><div class="side-lbl">Your State</div><select class="side-sel" id="chat-state"></select></div>
    <div class="side-lbl">Quick Questions</div>
    <div class="side-link" onclick="sq('How do I register to vote?')"><div class="side-link-ico">&#128203;</div>Register to vote</div>
    <div class="side-link" onclick="sq('What ID do I need to vote?')"><div class="side-link-ico">&#129306;</div>Voter ID rules</div>
    <div class="side-link" onclick="sq('How do I request a mail-in ballot?')"><div class="side-link-ico">&#9993;</div>Mail-in ballot</div>
    <div class="side-link" onclick="sq('When and where can I vote early?')"><div class="side-link-ico">&#128197;</div>Early voting</div>
    <div class="side-link" onclick="sq('How do I find my polling place?')"><div class="side-link-ico">&#128506;</div>Find polling place</div>
    <div class="side-link" onclick="sq('How do I check if I am registered to vote?')"><div class="side-link-ico">&#9989;</div>Check registration</div>
    <div class="side-link" onclick="sq('What is a provisional ballot?')"><div class="side-link-ico">&#9878;</div>Provisional ballots</div>
    <div class="side-link" onclick="sq('How do I update my voter registration address?')"><div class="side-link-ico">&#128260;</div>Update registration</div>
    <div class="side-link" onclick="sq('What are the voter registration deadlines?')"><div class="side-link-ico">&#128197;</div>Deadlines</div>
    <div class="side-link" onclick="sq('Can people with felony convictions vote in my state?')"><div class="side-link-ico">&#128220;</div>Rights restoration</div>
    <div class="side-bot">
      <a class="emer-card" href="https://866ourvote.org/" target="_blank" rel="noopener">
        <div class="emer-num">866-OUR-VOTE</div>
        <div class="emer-sub">&#128680; Election Protection</div>
      </a>
    </div>
  </div>
  <div class="chat-main">
    <div class="msgs" id="msgs">
      <div class="chat-welcome" id="chat-welcome">
        <div class="cw-ico">&#128441;</div>
        <div class="cw-h">VoterLens</div>
        <p class="cw-p">Ask me anything about voting in your state. Every answer cites official government sources.</p>
        <div class="cw-pills">
          <div class="cw-pill" onclick="sq('How do I register to vote?')">Register to vote</div>
          <div class="cw-pill" onclick="sq('What ID do I need?')">Voter ID</div>
          <div class="cw-pill" onclick="sq('Mail-in ballot?')">Mail-in</div>
          <div class="cw-pill" onclick="sq('Early voting?')">Early voting</div>
          <div class="cw-pill" onclick="sq('Find my polling place?')">Polling place</div>
        </div>
      </div>
    </div>
    <div class="ibar-wrap">
      <div class="ibar">
        <div class="ibar-row">
          <textarea class="ibar-ta" id="chat-ta" placeholder="Ask VoterLens anything about U.S. voting..." rows="1" onkeydown="handleKey(event)" oninput="autoH(this)"></textarea>
          <div class="ibar-btns">
            <button class="i-mic" id="mic-btn" onclick="toggleMic()" title="Voice input">&#127897;</button>
            <button class="i-send" onclick="sendMsg()">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </div>
        <div class="ibar-foot">
          <span class="ibar-note">Official Gov. Sources &middot; Nonpartisan &middot; Verify Locally</span>
          <a class="ibar-emer" href="https://866ourvote.org/" target="_blank">&#128680; 866-OUR-VOTE</a>
        </div>
      </div>
    </div>
  </div>
</div>

<script>

// ── THEME ──
var isDark=true;
function toggleTheme(){
  isDark=!isDark;
  document.documentElement.setAttribute('data-theme',isDark?'dark':'light');
  document.getElementById('theme-btn').textContent=isDark?'\u{1F319}':'\u2600\uFE0F';
  // Re-render SVG map colors after the theme flips so light mode never inherits dark fills/text.
  setTimeout(function(){ window.dispatchEvent(new Event('resize')); },80);
}

// ── MOBILE DRAWER ──
var drwOpen=false;
function toggleDrw(){
  drwOpen=!drwOpen;
  document.getElementById('mob-drawer').classList.toggle('open',drwOpen);
  var s=document.getElementById('ham').querySelectorAll('span');
  if(drwOpen){s[0].style.transform='rotate(45deg) translate(5px,5px)';s[1].style.opacity='0';s[2].style.transform='rotate(-45deg) translate(5px,-5px)';}
  else{s[0].style.transform='';s[1].style.opacity='1';s[2].style.transform='';}
}

// ── STATES ──
var STATES=[{n:"Alabama",a:"AL"},{n:"Alaska",a:"AK"},{n:"Arizona",a:"AZ"},{n:"Arkansas",a:"AR"},{n:"California",a:"CA"},{n:"Colorado",a:"CO"},{n:"Connecticut",a:"CT"},{n:"Delaware",a:"DE"},{n:"Florida",a:"FL"},{n:"Georgia",a:"GA"},{n:"Hawaii",a:"HI"},{n:"Idaho",a:"ID"},{n:"Illinois",a:"IL"},{n:"Indiana",a:"IN"},{n:"Iowa",a:"IA"},{n:"Kansas",a:"KS"},{n:"Kentucky",a:"KY"},{n:"Louisiana",a:"LA"},{n:"Maine",a:"ME"},{n:"Maryland",a:"MD"},{n:"Massachusetts",a:"MA"},{n:"Michigan",a:"MI"},{n:"Minnesota",a:"MN"},{n:"Mississippi",a:"MS"},{n:"Missouri",a:"MO"},{n:"Montana",a:"MT"},{n:"Nebraska",a:"NE"},{n:"Nevada",a:"NV"},{n:"New Hampshire",a:"NH"},{n:"New Jersey",a:"NJ"},{n:"New Mexico",a:"NM"},{n:"New York",a:"NY"},{n:"North Carolina",a:"NC"},{n:"North Dakota",a:"ND"},{n:"Ohio",a:"OH"},{n:"Oklahoma",a:"OK"},{n:"Oregon",a:"OR"},{n:"Pennsylvania",a:"PA"},{n:"Rhode Island",a:"RI"},{n:"South Carolina",a:"SC"},{n:"South Dakota",a:"SD"},{n:"Tennessee",a:"TN"},{n:"Texas",a:"TX"},{n:"Utah",a:"UT"},{n:"Vermont",a:"VT"},{n:"Virginia",a:"VA"},{n:"Washington",a:"WA"},{n:"West Virginia",a:"WV"},{n:"Wisconsin",a:"WI"},{n:"Wyoming",a:"WY"}];
var STATE_EXTRA={GA:["GA Secretary of State - Elections|https://sos.ga.gov/page/elections-voting","Georgia My Voter Page|https://mvp.sos.ga.gov/s/"],CA:["CA Secretary of State|https://www.sos.ca.gov/elections","Register to Vote CA|https://registertovote.ca.gov/"],TX:["TX Secretary of State|https://www.sos.texas.gov/elections/voter/","Vote Texas|https://www.votetexas.gov/"],NY:["NY Board of Elections|https://www.elections.ny.gov/"],FL:["FL Division of Elections|https://dos.florida.gov/elections/","Register FL|https://registertovoteflorida.gov/"],PA:["PA Dept of State|https://www.vote.pa.gov/"],OH:["OH Secretary of State|https://www.ohiosos.gov/elections/voters/"],MI:["MI Voter Info Center|https://mvic.sos.state.mi.us/"],IL:["IL State Board of Elections|https://www.elections.il.gov/"],AZ:["AZ Secretary of State|https://azsos.gov/elections"],WI:["WI Elections Commission|https://elections.wi.gov/"],NC:["NC State Board of Elections|https://www.ncsbe.gov/"],VA:["VA Dept of Elections|https://www.elections.virginia.gov/"],WA:["WA Secretary of State|https://www.sos.wa.gov/elections/"],CO:["CO Secretary of State|https://www.coloradosos.gov/voter/"],MN:["MN Secretary of State|https://www.sos.state.mn.us/elections-voting/"],OR:["OR Secretary of State|https://sos.oregon.gov/voting/"],NV:["NV Secretary of State|https://www.nvsos.gov/sos/elections"]};
function getSources(a,n){var base=["Vote.gov - Register in "+n+"|https://vote.gov/register/"+a.toLowerCase()+"/","EAC - Register and Vote|https://www.eac.gov/voters/register-and-vote-in-your-state","USA.gov - State Election Office|https://www.usa.gov/state-election-office","Election Protection (866-OUR-VOTE)|https://866ourvote.org/"];return[...(STATE_EXTRA[a]||[]),...base].map(function(s){var p=s.split('|');return{t:p[0],u:p[1]};});}
// Populate selects
var optHtml=STATES.map(function(s){return '<option value="'+s.a+'">'+s.n+'</option>';}).join('');
['home-state','chat-state'].forEach(function(id){var el=document.getElementById(id);if(el){el.innerHTML=optHtml;el.value='GA';}});

// ── CARDS ──
var CARDS=[{ic:'&#128203;',t:'Register to Vote',d:'Deadlines & online options',q:'How do I register to vote?'},{ic:'&#129306;',t:'Voter ID Rules',d:'Accepted IDs at the polls',q:'What ID do I need to vote?'},{ic:'&#9993;',t:'Mail-In Ballot',d:'Request, fill & return',q:'How do I request a mail-in or absentee ballot?'},{ic:'&#128197;',t:'Early Voting',d:'Dates, times & locations',q:'When and where can I vote early?'},{ic:'&#128506;',t:'Find Polling Place',d:'Your voting location',q:'How do I find my polling place?'},{ic:'&#9989;',t:'Check Registration',d:'Verify your status',q:'How do I check if I am registered to vote?'}];
document.getElementById('cards-grid').innerHTML=CARDS.map(function(c,i){return '<div class="q-card" style="transition-delay:'+(.08*i)+'s" onclick="cardClick(\''+c.q.replace(/'/g,"\\'")+'\')" ><div class="qc-icon">'+c.ic+'</div><div class="qc-title">'+c.t+'</div><div class="qc-desc">'+c.d+'</div><div class="qc-cta">Ask &#8594;</div></div>';}).join('');

// ── PAGE NAVIGATION ──
var currentPage='home';
function goPage(id){
  // hide all
  document.querySelectorAll('.page').forEach(function(p){p.classList.remove('active');p.style.display='';});
  var pg=document.getElementById('pg-'+id);
  if(id==='chat'){pg.style.display='flex';}
  else{pg.classList.add('active');}
  // nav active states
  ['home','chat'].forEach(function(k){
    var nb=document.getElementById('nb-'+k);
    var md=document.getElementById('md-'+k);
    if(nb)nb.classList.toggle('active',k===id);
    if(md)md.classList.toggle('active',k===id);
  });
  currentPage=id;
  if(drwOpen)toggleDrw();
  // scroll to top
  window.scrollTo(0,0);
  try{document.getElementById('pg-'+id).scrollTop=0;}catch(e){}
}

function hint(q){document.getElementById('home-ta').value=q;document.getElementById('home-ta').focus();}
function homeSubmit(){
  var q=document.getElementById('home-ta').value.trim();
  var st=document.getElementById('home-state').value;
  document.getElementById('chat-state').value=st;
  if(!q){document.getElementById('home-ta').focus();return;}
  goPage('chat');
  setTimeout(function(){document.getElementById('chat-ta').value=q;sendMsg();},80);
}
function cardClick(q){
  document.getElementById('chat-state').value=document.getElementById('home-state').value;
  goPage('chat');
  setTimeout(function(){document.getElementById('chat-ta').value=q;sendMsg();},80);
}
function sq(q){
  var ta=document.getElementById('chat-ta');
  if(ta){ta.value=q;ta.style.height='auto';}
  // Small delay so value is set before sendMsg reads it
  setTimeout(sendMsg, 10);
}

// ── CHAT ──
var conv=[],speakId=null,micOn=false,recog=null;
function autoH(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,120)+'px';}
function handleKey(e){
  if(e.key==='Enter'&&!e.shiftKey){
    e.preventDefault();
    // Prevent double-send if already loading
    var sending=document.querySelector('.msg-a .dots');
    if(!sending) sendMsg();
  }
}
function escH(s){return(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function md2h(md){
  return md
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/^### (.+)$/gm,'<h3>$1</h3>').replace(/^## (.+)$/gm,'<h2>$1</h2>').replace(/^# (.+)$/gm,'<h2>$1</h2>')
    .replace(/^\d+\. (.+)$/gm,'<li>$1</li>').replace(/^[-*] (.+)$/gm,'<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/gs,function(m){return '<ul>'+m+'</ul>';})
    .replace(/^---+$/gm,'<hr>').replace(/\n\n/g,'</p><p>').replace(/<p><\/p>/g,'')
    .replace(/<p>(<[hul])/g,'$1').replace(/(<\/[h23ul]>)<\/p>/g,'$1');
}
async function sendMsg(){
  var ta = document.getElementById('chat-ta');
  var q  = (ta.value || '').trim();
  if(!q) return;
  ta.value = ''; ta.style.height = 'auto';

  var abbr  = (document.getElementById('chat-state') || {value:'GA'}).value || 'GA';
  var stObj = (STATES||[]).find(function(s){return s.a===abbr;}) || {n:'Georgia',a:'GA'};
  var sources = typeof getSources==='function' ? getSources(abbr, stObj.n) : [];

  // Remove welcome screen
  var cw = document.getElementById('chat-welcome');
  if(cw) cw.remove();

  var msgsEl = document.getElementById('msgs');
  if(!msgsEl) return;

  // ── User bubble ────────────────────────────────────────────────────
  var uEl = document.createElement('div');
  uEl.className = 'msg-u';
  uEl.textContent = q;
  msgsEl.appendChild(uEl);
  scrollToBottom(msgsEl);

  // ── AI loading bubble ──────────────────────────────────────────────
  var mid  = 'm' + Date.now();
  var aEl  = document.createElement('div');
  aEl.className = 'msg-a';
  aEl.id = mid;
  aEl.innerHTML =
    '<div class="msg-a-head"><div class="vl-badge"><div class="vl-icon">VL</div>VoterLens</div></div>' +
    '<div class="msg-a-body"><div class="dots">' +
      '<div class="dots-balls"><span></span><span></span><span></span></div>' +
      '<span class="dots-label">Searching official sources\u2026</span>' +
    '</div></div>';
  msgsEl.appendChild(aEl);
  scrollToBottom(msgsEl);

  conv = conv || [];
  conv.push({role:'user', content:q});

  try {
    var srcList = sources.map(function(s){return '- ['+s.t+']('+s.u+')';}).join('\n');
    var sys =
      'You are VoterLens, a friendly, expert U.S. civic rights assistant created by Sayna Kaushik and Michael Evans. ' +
      'You help ALL Americans understand their voting rights, registration, and civic participation.\n\n' +
      'CORE RULES:\n' +
      '1. Answer ALL voting and civic questions: registration, voter ID, polling hours, early voting, mail-in/absentee ballots, provisional ballots, voting rights, felony re-enfranchisement, emergency voting situations, voter intimidation, challenged votes, polling place problems, ballot measures, and civic rights.\n' +
      '2. Tailor EVERY answer specifically to: ' + stObj.n + ' (' + abbr + '). State-specific rules vary enormously.\n' +
      '3. NEVER invent specific dates, locations, or deadlines. Always tell users to verify at official sources.\n' +
      '4. Answer emergency scenarios IMMEDIATELY and CLEARLY.\n' +
      '5. Use clear markdown: ## headings, numbered steps, short bullets.\n' +
      '6. End EVERY response with ## Sources using ALL these official links:\n' + srcList + '\n' +
      '7. For ANY poll problem, ALWAYS include: Election Protection 866-OUR-VOTE (https://866ourvote.org/).\n' +
      '8. Be warm, calm, reassuring, and never partisan. Never tell people who to vote for.';

    var msgs2 = conv.slice(-14).map(function(m){return {role:m.role, content:m.content};});
    msgs2[msgs2.length-1] = {role:'user', content:'State: '+stObj.n+' ('+abbr+')\n\nQuestion: '+q};

    // ── Show progress stages while waiting ──────────────────────────
    var stage = 0;
    var stages = [
      'Searching sources…',
      'Checking state rules…',
      'Verifying data…',
      'Preparing answer…'
    ];
    var progressTimer = setInterval(function(){
      stage = Math.min(stage + 1, stages.length - 1);
      var bodyEl = aEl.querySelector('.msg-a-body');
      if(bodyEl) {
        bodyEl.innerHTML =
          '<div class="dots">' +
            '<div class="dots-balls"><span></span><span></span><span></span></div>' +
            '<span class="dots-label">' + stages[stage] + '</span>' +
          '</div>';
      }
    }, 1800);

    // ── API call ─────────────────────────────────────────────────────
    var resp = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        max_tokens: 1200,
        system:     sys,
        messages:   msgs2
      })
    });

    clearInterval(progressTimer);

    if(!resp.ok) {
      var errBody = await resp.text().catch(function(){return '';});
      throw new Error('API error ' + resp.status + (errBody ? ': ' + errBody.slice(0,120) : ''));
    }

    var data = await resp.json();
    var ans  = (data.content||[]).map(function(b){return b.type==='text'?b.text:'';}).join('');
    if(!ans) ans = 'I wasn\'t able to generate a response. Please try again.';

    conv.push({role:'assistant', content:ans});

    // Extract source chips from URLs in the response
    var urls = Array.from(ans.matchAll(/https?:\/\/[^\s)\],"<]+/g))
      .map(function(m){return m[0];})
      .filter(function(v,i,a){return a.indexOf(v)===i;})
      .slice(0, 8);

    var chips = urls.length
      ? '<div class="src-chips">' + urls.map(function(u){
          var l = u.replace(/^https?:\/\//,'');
          if(l.length > 38) l = l.slice(0,37) + '\u2026';
          return '<a class="src-chip" href="'+u+'" target="_blank" rel="noopener">&#128279; '+l+'</a>';
        }).join('') + '</div>'
      : '';

    // ── Render the answer ──────────────────────────────────────────
    var el = document.getElementById(mid);
    if(el) {
      el.innerHTML =
        '<div class="msg-a-head">' +
          '<div class="vl-badge"><div class="vl-icon">VL</div>VoterLens &mdash; ' + stObj.n + '</div>' +
          '<div class="msg-btns">' +
            '<button class="m-btn spk" id="spk-'+mid+'" onclick="doSpeak(\''+mid+'\',this)">&#9654; Listen</button>' +
            '<button class="m-btn" onclick="clearChat()">Clear</button>' +
          '</div>' +
        '</div>' +
        '<div class="msg-a-body">' + (typeof md2h==='function'?md2h(ans):ans) + '</div>' +
        chips;
    }

    // Badge tracking
    if(typeof earnBadge==='function') earnBadge('firstask');
    if(typeof chatCount!=='undefined') {
      chatCount++;
      try{localStorage.setItem('vl_chat_count', chatCount);}catch(e2){}
      if(chatCount >= 5 && typeof earnBadge==='function') earnBadge('chat5');
    }

  } catch(err) {
    var el2 = document.getElementById(mid);
    if(el2) {
      el2.querySelector('.msg-a-body').innerHTML =
        '<p style="color:#f87171;font-size:13px">' +
          '<strong>Unable to reach VoterLens.</strong> ' +
          'Please check your connection and try again. ' +
          '<br><small style="opacity:.7">' + escH(String(err)) + '</small>' +
        '</p>';
    }
    if(typeof conv!=='undefined' && conv.length > 0) conv.pop();
  }

  // ── Scroll to show the answer ───────────────────────────────────
  requestAnimationFrame(function(){
    scrollToBottom(msgsEl);
  });
}

// Reliable scroll-to-bottom that works with flex column layout
function scrollToBottom(el) {
  if(!el) return;
  // Use requestAnimationFrame to wait for DOM paint
  requestAnimationFrame(function(){
    el.scrollTop = el.scrollHeight;
  });
}
function clearChat(){
  conv=[];
  var m=document.getElementById('msgs');
  if(m){m.innerHTML='<div class="chat-welcome" id="chat-welcome"><div class="cw-ico">&#128441;</div><div class="cw-h">VoterLens</div><p class="cw-p">Ask me anything about voting in your state.</p><div class="cw-pills"><div class="cw-pill" onclick="sq(\'How do I register to vote?\')">Register to vote</div><div class="cw-pill" onclick="sq(\'Voter ID?\')">Voter ID</div><div class="cw-pill" onclick="sq(\'Mail-in ballot?\')">Mail-in</div></div></div>';m.scrollTop=0;}
}
function doSpeak(id,btn){if(speakId===id){window.speechSynthesis.cancel();speakId=null;btn.innerHTML='&#9654; Listen';return;}window.speechSynthesis.cancel();speakId=id;btn.innerHTML='&#9632; Stop';var el=document.getElementById(id);var txt=el?el.querySelector('.msg-a-body').innerText||'':'';var u=new SpeechSynthesisUtterance(txt);u.rate=.94;u.onend=function(){speakId=null;btn.innerHTML='&#9654; Listen';};window.speechSynthesis.speak(u);}
function toggleMic(){var b=document.getElementById('mic-btn');if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){alert('Voice input requires Chrome.');return;}if(micOn){if(recog)recog.stop();micOn=false;b.classList.remove('on');return;}var SR=window.SpeechRecognition||window.webkitSpeechRecognition;recog=new SR();recog.continuous=false;recog.interimResults=false;recog.onresult=function(e){document.getElementById('chat-ta').value=e.results[0][0].transcript;micOn=false;b.classList.remove('on');};recog.onend=function(){micOn=false;b.classList.remove('on');};recog.start();micOn=true;b.classList.add('on');}

// ── SCROLL REVEAL ──
function revealOnScroll(){
  var els=document.querySelectorAll('.info-card,.q-card,.about-card');
  var vH=window.innerHeight;
  els.forEach(function(el){
    var r=el.getBoundingClientRect();
    if(r.top<vH-60)el.classList.add('visible');
  });
}
window.addEventListener('scroll',revealOnScroll,{passive:true});
document.querySelectorAll('.page').forEach(function(p){p.addEventListener('scroll',revealOnScroll,{passive:true});});
setTimeout(revealOnScroll,300);

// ── WEBGL NEBULA BACKGROUND ──
(function(){
  var c=document.getElementById('bg-canvas');if(!c)return;
  var gl=c.getContext('webgl',{alpha:true,antialias:false});if(!gl)return;
  var W=0,H=0;
  function rsz(){W=c.width=window.innerWidth;H=c.height=window.innerHeight;gl.viewport(0,0,W,H);}
  rsz();window.addEventListener('resize',rsz);
  function mkSh(src,t){var s=gl.createShader(t);gl.shaderSource(s,src);gl.compileShader(s);return s;}
  var VS='attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}';
  var FS='precision mediump float;uniform vec2 R;uniform float T;uniform vec2 M;uniform float DARK;float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5);}float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*n(p);p*=2.1;a*=.5;}return v;}void main(){vec2 uv=(gl_FragCoord.xy/R)*2.-1.;uv.x*=R.x/R.y;vec2 m=(M/R)*2.-1.;m.x*=R.x/R.y;float t=T*.08;vec2 q=vec2(fbm(uv+t*.6),fbm(uv+vec2(1.7,9.2)+t*.5));vec2 r=vec2(fbm(uv+2.*q+t*.25),fbm(uv+2.*q+vec2(8.3,2.8)+t*.18));float f=fbm(uv+2.*r);vec3 dark=vec3(.01,.02,.07);dark=mix(dark,vec3(.08,.01,.01),clamp((uv.x*.5+.5)*f*f*2.5,0.,1.));dark=mix(dark,vec3(.01,.04,.12),clamp((1.-(uv.x*.5+.5))*f*1.5,0.,1.));dark+=.04*vec3(.1,.1,.6)*fbm(uv*4.+t);dark*=.7+f*.7;vec3 light=vec3(.88,.9,1.);light=mix(light,vec3(.95,.85,.85),clamp(f*f*1.5,0.,1.));light=mix(light,vec3(.85,.88,.98),clamp((1.-f)*1.2,0.,1.));light*=.92+f*.1;vec3 col=mix(light,dark,DARK);vec2 sg=uv*80.;float hv=h(floor(sg));if(hv>.984&&DARK>.5){float d=length(fract(sg)-.5);float tw=sin(T*2.2+hv*28.)*.3+.7;col+=hv*.5*tw*smoothstep(.25,0.,d)*vec3(.95,.96,1.);}float ml=length(uv-m);col+=DARK*.025*vec3(.7,.5,.1)/(ml*ml+.45);col*=smoothstep(2.,.25,length(uv));gl_FragColor=vec4(col,DARK*.9+(1.-DARK)*.3);}';
  var prog=gl.createProgram();
  gl.attachShader(prog,mkSh(VS,gl.VERTEX_SHADER));gl.attachShader(prog,mkSh(FS,gl.FRAGMENT_SHADER));
  gl.linkProgram(prog);gl.useProgram(prog);
  var buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
  var pLoc=gl.getAttribLocation(prog,'p');gl.enableVertexAttribArray(pLoc);gl.vertexAttribPointer(pLoc,2,gl.FLOAT,false,0,0);
  var uR=gl.getUniformLocation(prog,'R'),uT=gl.getUniformLocation(prog,'T'),uM=gl.getUniformLocation(prog,'M'),uD=gl.getUniformLocation(prog,'DARK');
  var mx=W/2,my=H/2,darkVal=1.0,targetDark=1.0;
  document.addEventListener('mousemove',function(e){mx=e.clientX;my=e.clientY;});
  document.addEventListener('touchmove',function(e){mx=e.touches[0].clientX;my=e.touches[0].clientY;},{passive:true});
  // Watch theme changes
  var observer=new MutationObserver(function(){targetDark=document.documentElement.getAttribute('data-theme')==='light'?0.0:1.0;});
  observer.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
  var t0=performance.now();
  gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
  (function loop(){
    darkVal+=(targetDark-darkVal)*.04;
    var t=(performance.now()-t0)/1000;
    gl.uniform2f(uR,W,H);gl.uniform1f(uT,t);gl.uniform2f(uM,mx,H-my);gl.uniform1f(uD,darkVal);
    gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
    requestAnimationFrame(loop);
  })();
})();


// ════════════════════════════════════════════════════════════════════════
// GLOBE + USA MAP  — Complete Rewrite for Accuracy
// ════════════════════════════════════════════════════════════════════════

// ── STATE DATA ──────────────────────────────────────────────────────────
var MAP_STATE_DATA = {
  AL:{name:'Alabama',ev:9,reg:'15 days before election',id:'Photo ID required',early:'Yes',absentee:'Excuse required',lean:'solid-r'},
  AK:{name:'Alaska',ev:3,reg:'30 days before election',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  AZ:{name:'Arizona',ev:11,reg:'29 days before election',id:'ID required',early:'Yes',absentee:'No excuse',lean:'swing'},
  AR:{name:'Arkansas',ev:6,reg:'30 days before election',id:'Photo ID required',early:'Yes',absentee:'Excuse required',lean:'solid-r'},
  CA:{name:'California',ev:54,reg:'15 days (online)',id:'No ID required',early:'Yes',absentee:'Auto-mailed to all',lean:'solid-b'},
  CO:{name:'Colorado',ev:10,reg:'8 days before',id:'No ID required',early:'Yes',absentee:'Auto-mailed to all',lean:'solid-b'},
  CT:{name:'Connecticut',ev:7,reg:'7 days before',id:'First-timers only',early:'Limited',absentee:'No excuse',lean:'solid-b'},
  DE:{name:'Delaware',ev:3,reg:'24 days before',id:'First-timers only',early:'Yes',absentee:'No excuse',lean:'solid-b'},
  FL:{name:'Florida',ev:30,reg:'29 days before',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'lean-r'},
  GA:{name:'Georgia',ev:16,reg:'28 days before',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'swing'},
  HI:{name:'Hawaii',ev:4,reg:'10 days before',id:'No ID required',early:'Yes',absentee:'Auto-mailed to all',lean:'solid-b'},
  ID:{name:'Idaho',ev:4,reg:'Election Day',id:'ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  IL:{name:'Illinois',ev:19,reg:'Election Day',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'solid-b'},
  IN:{name:'Indiana',ev:11,reg:'29 days before',id:'Photo ID required',early:'Yes',absentee:'Excuse required',lean:'solid-r'},
  IA:{name:'Iowa',ev:6,reg:'Election Day',id:'ID required',early:'Yes',absentee:'No excuse',lean:'lean-r'},
  KS:{name:'Kansas',ev:6,reg:'21 days before',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  KY:{name:'Kentucky',ev:8,reg:'28 days before',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  LA:{name:'Louisiana',ev:8,reg:'30 days before',id:'Photo ID required',early:'Yes',absentee:'Excuse required',lean:'solid-r'},
  ME:{name:'Maine',ev:4,reg:'Election Day',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'lean-b'},
  MD:{name:'Maryland',ev:10,reg:'21 days before',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'solid-b'},
  MA:{name:'Massachusetts',ev:11,reg:'20 days before',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'solid-b'},
  MI:{name:'Michigan',ev:15,reg:'Election Day',id:'No ID required',early:'Yes',absentee:'Auto-mailed to all',lean:'swing'},
  MN:{name:'Minnesota',ev:10,reg:'Election Day',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'lean-b'},
  MS:{name:'Mississippi',ev:6,reg:'30 days before',id:'Photo ID required',early:'Yes',absentee:'Excuse required',lean:'solid-r'},
  MO:{name:'Missouri',ev:10,reg:'28 days before',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  MT:{name:'Montana',ev:4,reg:'Election Day',id:'ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  NE:{name:'Nebraska',ev:5,reg:'15 days before',id:'ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  NV:{name:'Nevada',ev:6,reg:'4 days before',id:'ID required',early:'Yes',absentee:'Auto-mailed to all',lean:'swing'},
  NH:{name:'New Hampshire',ev:4,reg:'Election Day',id:'ID required',early:'Limited',absentee:'Excuse required',lean:'lean-b'},
  NJ:{name:'New Jersey',ev:14,reg:'21 days before',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'solid-b'},
  NM:{name:'New Mexico',ev:5,reg:'28 days before',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'solid-b'},
  NY:{name:'New York',ev:28,reg:'25 days before',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'solid-b'},
  NC:{name:'North Carolina',ev:16,reg:'25 days before',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'swing'},
  ND:{name:'North Dakota',ev:3,reg:'No registration',id:'ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  OH:{name:'Ohio',ev:17,reg:'30 days before',id:'ID required',early:'Yes',absentee:'No excuse',lean:'lean-r'},
  OK:{name:'Oklahoma',ev:7,reg:'25 days before',id:'ID required',early:'Yes',absentee:'Excuse required',lean:'solid-r'},
  OR:{name:'Oregon',ev:8,reg:'21 days before',id:'No ID required',early:'Yes',absentee:'Auto-mailed to all',lean:'solid-b'},
  PA:{name:'Pennsylvania',ev:19,reg:'15 days before',id:'First-timers only',early:'Yes',absentee:'No excuse',lean:'swing'},
  RI:{name:'Rhode Island',ev:4,reg:'30 days before',id:'ID required',early:'Yes',absentee:'No excuse',lean:'solid-b'},
  SC:{name:'South Carolina',ev:9,reg:'30 days before',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'lean-r'},
  SD:{name:'South Dakota',ev:3,reg:'15 days before',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  TN:{name:'Tennessee',ev:11,reg:'30 days before',id:'Photo ID required',early:'Yes',absentee:'Excuse required',lean:'solid-r'},
  TX:{name:'Texas',ev:40,reg:'30 days before',id:'Photo ID required',early:'Yes',absentee:'65+ no excuse',lean:'lean-r'},
  UT:{name:'Utah',ev:6,reg:'7 days before',id:'ID required',early:'Yes',absentee:'Auto-mailed to all',lean:'lean-r'},
  VT:{name:'Vermont',ev:3,reg:'Election Day',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'solid-b'},
  VA:{name:'Virginia',ev:13,reg:'15 days before',id:'ID required',early:'Yes',absentee:'No excuse',lean:'lean-b'},
  WA:{name:'Washington',ev:12,reg:'8 days before',id:'No ID required',early:'Yes',absentee:'Auto-mailed to all',lean:'solid-b'},
  WV:{name:'West Virginia',ev:4,reg:'21 days before',id:'ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  WI:{name:'Wisconsin',ev:10,reg:'Election Day',id:'Photo ID required',early:'Yes',absentee:'No excuse',lean:'swing'},
  WY:{name:'Wyoming',ev:3,reg:'14 days before',id:'ID required',early:'Yes',absentee:'No excuse',lean:'solid-r'},
  DC:{name:'D.C.',ev:3,reg:'30 days before',id:'No ID required',early:'Yes',absentee:'No excuse',lean:'solid-b'}
};

// Accurate state shapes — Albers USA projection, 960×600 viewBox
// These match the standard US Census/D3.js US map layout exactly
var STATE_PATHS = {
  WA:[[124,67],[178,67],[178,100],[168,114],[152,119],[136,115],[122,116],[108,120],[104,109],[124,67]],
  OR:[[104,109],[122,116],[136,115],[152,119],[168,114],[178,100],[180,154],[162,167],[140,170],[104,170],[104,155],[104,109]],
  CA:[[104,170],[140,170],[162,167],[180,154],[183,200],[173,234],[163,268],[149,282],[131,272],[112,244],[104,214],[104,170]],
  NV:[[148,112],[178,100],[212,115],[216,158],[200,182],[183,200],[173,234],[163,268],[157,200],[168,114],[148,112]],
  ID:[[178,67],[228,67],[238,122],[221,142],[212,115],[178,100],[178,67]],
  MT:[[178,67],[318,67],[325,97],[305,107],[274,110],[238,122],[228,67],[178,67]],
  WY:[[212,115],[238,122],[325,97],[332,132],[327,158],[212,158],[212,115]],
  UT:[[200,158],[216,158],[212,115],[168,114],[163,200],[200,235],[216,235],[220,198],[200,158]],
  CO:[[212,158],[327,158],[334,188],[212,188],[212,158]],
  AZ:[[163,268],[200,265],[220,265],[220,314],[200,334],[183,338],[161,323],[151,298],[163,268]],
  NM:[[212,188],[334,188],[340,229],[278,263],[220,268],[216,238],[212,188]],
  ND:[[274,67],[404,67],[412,87],[394,102],[325,97],[274,67]],
  SD:[[274,110],[325,97],[394,102],[404,122],[400,142],[274,142],[274,110]],
  NE:[[274,142],[400,142],[404,162],[404,178],[325,178],[274,172],[274,142]],
  KS:[[274,178],[404,178],[412,198],[412,214],[274,214],[274,178]],
  OK:[[274,214],[412,214],[420,242],[384,258],[314,258],[274,242],[274,214]],
  TX:[[274,242],[314,258],[384,258],[420,242],[440,278],[450,314],[445,363],[410,393],[364,398],[324,388],[294,363],[268,323],[252,292],[249,268],[274,242]],
  MN:[[394,67],[494,67],[504,92],[499,117],[474,132],[424,132],[404,122],[394,102],[394,67]],
  IA:[[404,132],[474,132],[499,117],[514,137],[509,162],[404,162],[404,132]],
  MO:[[404,162],[509,162],[514,182],[514,208],[494,228],[470,233],[444,238],[420,222],[412,214],[412,198],[404,178],[404,162]],
  AR:[[420,238],[494,232],[514,238],[517,268],[494,283],[444,283],[420,268],[420,238]],
  LA:[[420,283],[444,283],[494,283],[517,283],[520,303],[504,314],[484,329],[460,334],[434,319],[420,303],[420,283]],
  WI:[[470,67],[544,67],[560,92],[550,117],[534,132],[499,117],[494,67],[470,67]],
  MI:[[534,68],[594,68],[604,88],[594,108],[574,117],[555,110],[544,92],[534,68]],
  IL:[[499,117],[534,132],[550,147],[544,178],[534,212],[514,228],[514,208],[514,182],[514,162],[514,137],[499,117]],
  IN:[[550,147],[585,147],[594,178],[584,212],[564,222],[550,208],[544,178],[550,147]],
  OH:[[585,122],[630,122],[644,153],[640,188],[620,202],[594,197],[584,212],[594,178],[585,147],[585,122]],
  KY:[[514,228],[564,222],[584,212],[620,202],[640,218],[635,238],[604,253],[570,258],[544,253],[514,243],[514,228]],
  TN:[[514,243],[544,253],[570,258],[604,253],[644,248],[664,263],[640,278],[584,278],[514,273],[514,243]],
  MS:[[494,283],[517,268],[517,283],[520,303],[514,338],[494,349],[474,334],[459,298],[494,283]],
  AL:[[494,283],[459,298],[474,334],[494,349],[514,353],[530,323],[534,293],[514,283],[494,283]],
  GA:[[534,268],[584,268],[604,253],[644,248],[654,273],[644,314],[620,334],[584,338],[564,323],[544,298],[534,268]],
  FL:[[544,338],[564,323],[584,338],[620,334],[644,354],[654,374],[645,404],[624,419],[604,424],[584,419],[565,404],[555,389],[549,368],[544,338]],
  SC:[[604,253],[644,248],[664,263],[664,293],[644,314],[620,334],[604,314],[604,283],[604,253]],
  NC:[[584,233],[640,218],[674,228],[699,243],[704,263],[664,263],[644,248],[604,253],[584,243],[584,233]],
  VA:[[584,203],[640,203],[674,213],[699,203],[720,218],[704,238],[704,263],[699,243],[674,228],[640,218],[584,233],[584,203]],
  WV:[[584,178],[640,178],[654,198],[644,218],[620,222],[604,213],[584,203],[584,178]],
  PA:[[584,148],[684,148],[699,163],[699,183],[684,193],[640,188],[630,122],[585,122],[584,148]],
  NY:[[584,108],[654,103],[699,103],[724,118],[720,143],[699,148],[699,163],[684,148],[584,148],[584,122],[584,108]],
  VT:[[699,67],[734,67],[739,97],[724,118],[699,103],[699,67]],
  NH:[[734,67],[759,67],[764,93],[754,118],[739,118],[724,118],[739,97],[734,67]],
  ME:[[759,67],[805,67],[815,83],[804,108],[780,118],[759,103],[764,93],[759,67]],
  MA:[[699,103],[739,103],[759,103],[764,118],[744,128],[724,128],[699,113],[699,103]],
  RI:[[764,118],[780,118],[780,133],[764,133],[764,118]],
  CT:[[724,128],[749,123],[764,133],[754,145],[724,140],[724,128]],
  NJ:[[720,143],[744,138],[754,153],[744,168],[724,168],[720,153],[720,143]],
  DE:[[739,158],[754,153],[759,168],[744,178],[736,168],[739,158]],
  MD:[[699,163],[739,158],[739,168],[744,178],[724,188],[704,183],[699,168],[699,163]],
  DC:[[716,174],[724,169],[724,177],[716,177],[716,174]],
  AK:[[30,395],[155,395],[175,445],[163,480],[120,495],[70,490],[30,465],[30,395]],
  HI:[[252,464],[285,464],[290,484],[274,494],[252,489],[252,464]],
};

// Label positions (center of each state for abbreviation text)
var STATE_LABEL_POS = {
  WA:[138,97],  OR:[140,146], CA:[136,224], NV:[184,176], ID:[207,107],
  MT:[252,90],  WY:[270,130], UT:[197,200], CO:[270,172], AZ:[188,298],
  NM:[268,227], ND:[344,84],  SD:[344,120], NE:[344,158], KS:[344,195],
  OK:[344,229], TX:[348,318], MN:[448,103], IA:[456,147], MO:[462,197],
  AR:[464,257], LA:[466,305], WI:[520,102], MI:[562,90],  IL:[524,178],
  IN:[566,183], OH:[608,167], KY:[574,237], TN:[580,261], MS:[490,315],
  AL:[494,318], GA:[588,296], FL:[596,382], SC:[634,282], NC:[638,253],
  VA:[648,225], WV:[618,198], PA:[638,167], NY:[636,130], VT:[716,88],
  NH:[744,96],  ME:[783,92],  MA:[732,116], RI:[772,125], CT:[738,134],
  NJ:[734,156], DE:[748,163], MD:[720,173], DC:[720,173],
  AK:[103,444], HI:[271,478],
};

// Lean colors (rich, saturated, like a real political map)
function leanFill(lean, hovered){
  if(hovered) return {fill:'#e8f4ff',stroke:'#1a1a2e',sw:1.5,shadow:'rgba(30,144,255,0.6)'};
  var map = {
    'solid-r': {fill:'#c0392b',stroke:'#7b1c12',sw:0.5,shadow:'rgba(192,57,43,0.4)'},
    'lean-r':  {fill:'#e74c3c',stroke:'#922b21',sw:0.5,shadow:'rgba(231,76,60,0.3)'},
    'swing':   {fill:'#e8a020',stroke:'#9d6800',sw:0.8,shadow:'rgba(232,160,32,0.5)'},
    'lean-b':  {fill:'#2980b9',stroke:'#1a5276',sw:0.5,shadow:'rgba(41,128,185,0.3)'},
    'solid-b': {fill:'#1a5da8',stroke:'#0e3a6e',sw:0.5,shadow:'rgba(26,93,168,0.4)'},
  };
  return map[lean] || {fill:'#2c3e50',stroke:'#1a252f',sw:0.5,shadow:'none'};
}

// Battleground state cards
var BATTLEGROUNDS=[
  {name:'Pennsylvania',abbr:'PA',ev:19,lat:41.0,lon:-77.5,type:'swing',lean:'Swing State'},
  {name:'Michigan',abbr:'MI',ev:15,lat:44.3,lon:-84.5,type:'swing',lean:'Swing State'},
  {name:'Wisconsin',abbr:'WI',ev:10,lat:44.5,lon:-89.5,type:'swing',lean:'Swing State'},
  {name:'Arizona',abbr:'AZ',ev:11,lat:34.0,lon:-111.5,type:'swing',lean:'Swing State'},
  {name:'Nevada',abbr:'NV',ev:6,lat:38.8,lon:-116.5,type:'swing',lean:'Swing State'},
  {name:'Georgia',abbr:'GA',ev:16,lat:32.6,lon:-83.4,type:'swing',lean:'Swing State'},
  {name:'North Carolina',abbr:'NC',ev:16,lat:35.5,lon:-79.5,type:'lean-r',lean:'Leans R'},
  {name:'Florida',abbr:'FL',ev:30,lat:27.7,lon:-81.5,type:'lean-r',lean:'Leans R'},
  {name:'Texas',abbr:'TX',ev:40,lat:31.0,lon:-100.0,type:'lean-r',lean:'Leans R'},
  {name:'Minnesota',abbr:'MN',ev:10,lat:46.4,lon:-93.1,type:'lean-b',lean:'Leans D'},
  {name:'New Hampshire',abbr:'NH',ev:4,lat:43.7,lon:-71.6,type:'lean-b',lean:'Leans D'},
  {name:'Virginia',abbr:'VA',ev:13,lat:37.8,lon:-79.4,type:'lean-b',lean:'Leans D'},
];
var TC={'swing':'#e8a020','lean-r':'#e74c3c','lean-b':'#2980b9'};
(function(){
  var g=document.getElementById('state-cards');
  if(!g)return;
  g.innerHTML=BATTLEGROUNDS.map(function(s){
    var c=TC[s.type],cls='state-card sc-'+s.type;
    return '<div class="'+cls+'" onclick="cardClick(\'What are the voting requirements in '+s.name+'?\')">'
      +'<div class="sc-dot" style="background:'+c+';box-shadow:0 0 7px '+c+'"></div>'
      +'<div class="sc-info"><div class="sc-name">'+s.name+'</div>'
      +'<div class="sc-ev">'+s.ev+' electoral votes</div>'
      +'<div class="sc-status sc-t-'+s.type+'">'+s.lean+'</div></div></div>';
  }).join('');
})();

// ════════════════════════════════════════════════════════════════════
// GLOBE BUILDER — draws real world geography using lat/lon polygons
// ════════════════════════════════════════════════════════════════════
function makeGlobeTexture(W,H,showBattleground){
  var tc=document.createElement('canvas');tc.width=W;tc.height=H;
  var cx=tc.getContext('2d');

  // Deep ocean
  var og=cx.createLinearGradient(0,0,0,H);
  og.addColorStop(0,'#081426');og.addColorStop(0.5,'#0a1a30');og.addColorStop(1,'#060f1e');
  cx.fillStyle=og;cx.fillRect(0,0,W,H);

  // Convert lon/lat to canvas pixel
  function px(lon,lat){return [(lon+180)/360*W,(90-lat)/180*H];}

  // Draw a polygon from [[lon,lat],...] array
  function land(pts,fill){
    if(!pts||pts.length<2)return;
    cx.beginPath();
    pts.forEach(function(p,i){var q=px(p[0],p[1]);if(i===0)cx.moveTo(q[0],q[1]);else cx.lineTo(q[0],q[1]);});
    cx.closePath();
    cx.fillStyle=fill;cx.fill();
  }
  function outline(pts,col,lw){
    if(!pts||pts.length<2)return;
    cx.beginPath();
    pts.forEach(function(p,i){var q=px(p[0],p[1]);if(i===0)cx.moveTo(q[0],q[1]);else cx.lineTo(q[0],q[1]);});
    cx.closePath();
    cx.strokeStyle=col;cx.lineWidth=lw||0.5;cx.stroke();
  }

  var LAND='#1a3d6b', LAND2='rgba(20,50,90,0.5)';
  var STROKE='rgba(45,100,180,0.25)';

  // ── NORTH AMERICA ───────────────────────────────────────────────
  land([[-168,72],[-162,70],[-155,72],[-150,60],[-142,60],[-133,58],[-130,55],[-125,50],
        [-124,48],[-120,49],[-110,49],[-96,49],[-88,48],[-84,46],[-82,44],[-76,44],
        [-75,45],[-72,41],[-67,47],[-65,44],[-64,45],[-66,45],[-70,43],[-71,41],
        [-74,39],[-75,38],[-76,35],[-80,32],[-81,30],[-85,30],[-88,30],[-90,29],
        [-97,26],[-100,25],[-105,30],[-109,31],[-114,32],[-117,32],[-118,34],
        [-120,37],[-124,37],[-124,42],[-124,48],[-125,50],[-130,55],[-133,58],
        [-142,60],[-150,60],[-155,60],[-160,60],[-165,62],[-168,66],[-168,72]],LAND);
  outline([[-168,72],[-155,72],[-142,60],[-133,58],[-130,55],[-125,50],[-124,48],[-120,49],[-110,49],[-96,49],[-88,48],[-84,46],[-75,45],[-72,41],[-67,47],[-65,44],[-64,45],[-70,43],[-71,41],[-74,39],[-75,38],[-76,35],[-80,32],[-88,30],[-97,26],[-105,30],[-114,32],[-117,32],[-124,37],[-124,42],[-124,48],[-130,55],[-142,60],[-150,60],[-160,60],[-168,66],[-168,72]],STROKE,0.8);

  // Alaska (separate peninsula/islands region)
  land([[-168,66],[-165,62],[-162,60],[-156,58],[-150,58],[-148,60],[-152,62],[-158,62],[-162,63],[-166,64],[-168,66]],LAND);

  // Central America
  land([[-92,18],[-88,18],[-83,10],[-77,8],[-77,10],[-82,12],[-85,14],[-88,16],[-90,16],[-92,18]],LAND);

  // Caribbean
  land([[-77,20],[-74,20],[-74,18],[-77,18],[-77,20]],'rgba(26,61,107,0.7)');
  land([[-73,20],[-70,20],[-70,18],[-73,18],[-73,20]],'rgba(26,61,107,0.7)');

  // GREENLAND
  land([[-56,83],[-30,84],[-18,82],[-14,78],[-20,72],[-28,70],[-44,70],[-52,74],[-58,78],[-56,83]],LAND);
  outline([[-56,83],[-30,84],[-18,82],[-14,78],[-20,72],[-28,70],[-44,70],[-52,74],[-58,78],[-56,83]],STROKE,0.6);

  // SOUTH AMERICA
  land([[-80,12],[-77,8],[-75,5],[-72,12],[-65,10],[-60,8],[-52,5],[-50,2],
        [-48,0],[-44,-3],[-40,-5],[-38,-10],[-36,-14],[-36,-22],[-40,-22],
        [-44,-23],[-48,-28],[-52,-33],[-56,-38],[-62,-42],[-66,-44],[-68,-55],
        [-72,-48],[-74,-44],[-72,-38],[-70,-30],[-70,-18],[-75,-10],[-80,-5],[-80,12]],LAND);
  outline([[-80,12],[-72,12],[-52,5],[-50,2],[-44,-3],[-38,-10],[-36,-22],[-44,-23],[-52,-33],[-62,-42],[-68,-55],[-72,-38],[-70,-18],[-75,-10],[-80,-5],[-80,12]],STROKE,0.8);

  // EUROPE
  land([[-10,38],[-8,36],[-6,37],[0,38],[3,44],[5,43],[8,44],[12,44],[16,40],[18,40],
        [22,38],[26,38],[30,38],[34,38],[36,42],[36,48],[30,52],[26,54],[22,56],
        [18,60],[14,58],[12,57],[8,56],[4,52],[2,52],[-2,50],[-4,48],[-8,44],[-10,38]],LAND);
  outline([[-10,38],[0,38],[8,44],[16,40],[22,38],[30,38],[36,42],[36,48],[28,52],[22,56],[18,60],[12,57],[8,56],[2,52],[-4,48],[-8,44],[-10,38]],STROKE,0.7);

  // Scandinavia
  land([[4,58],[6,58],[10,57],[14,57],[18,58],[22,62],[26,64],[28,68],[26,70],
        [22,70],[18,70],[16,68],[14,65],[10,62],[8,60],[4,58]],LAND);
  land([[14,57],[22,56],[26,54],[28,56],[26,60],[22,62],[18,58],[14,57]],LAND);

  // British Isles
  land([[-6,50],[-2,50],[0,52],[2,52],[-2,54],[-4,56],[-6,58],[-8,58],[-8,54],[-6,50]],LAND);
  land([[-10,52],[-6,52],[-6,54],[-10,54],[-10,52]],'rgba(26,61,107,0.8)');

  // Iceland
  land([[-24,64],[-14,64],[-14,66],[-18,66],[-24,65],[-24,64]],'rgba(26,61,107,0.8)');

  // AFRICA
  land([[-18,16],[-16,14],[-12,14],[-8,12],[-4,10],[0,10],[4,6],[8,4],[10,6],
        [14,8],[18,8],[22,10],[26,10],[32,10],[36,10],[40,12],[44,10],[44,4],
        [42,0],[40,-4],[36,-10],[34,-18],[32,-26],[28,-34],[26,-36],[22,-36],
        [18,-34],[16,-28],[12,-26],[8,-20],[6,-14],[4,-10],[2,-6],[0,-4],
        [-4,-2],[-6,2],[-8,4],[-12,8],[-16,12],[-18,16]],LAND);
  outline([[-18,16],[-8,12],[0,10],[8,4],[14,8],[22,10],[36,10],[44,10],[44,4],[40,-4],[34,-18],[28,-34],[22,-36],[16,-28],[8,-20],[0,-4],[-6,2],[-12,8],[-18,16]],STROKE,0.8);

  // Madagascar
  land([[44,-12],[50,-12],[52,-16],[50,-20],[46,-20],[44,-16],[44,-12]],LAND);

  // ASIA (main Eurasia continent)
  land([[36,42],[40,40],[44,38],[48,34],[52,28],[56,24],[60,24],[64,22],
        [70,22],[74,24],[76,28],[80,26],[84,26],[88,28],[92,24],[96,22],
        [100,20],[102,22],[106,22],[108,20],[110,22],[114,22],[118,24],
        [120,24],[122,30],[124,32],[130,36],[132,40],[136,42],[138,44],
        [140,44],[140,48],[136,54],[130,60],[124,65],[120,66],[112,72],
        [100,72],[88,72],[78,68],[68,78],[56,72],[48,68],[44,68],
        [40,64],[36,60],[34,54],[30,50],[28,46],[28,44],[32,42],[36,42]],LAND);
  outline([[36,42],[44,38],[52,28],[60,24],[70,22],[80,26],[88,28],[96,22],[106,22],[114,22],[122,30],[132,40],[140,44],[140,48],[130,60],[120,66],[100,72],[78,68],[56,72],[44,68],[36,60],[30,50],[28,46],[32,42],[36,42]],STROKE,0.8);

  // Japan
  land([[130,32],[132,32],[136,34],[138,36],[140,38],[138,40],[136,38],[132,36],[130,34],[130,32]],'rgba(26,61,107,0.85)');

  // Indian subcontinent
  land([[62,24],[66,22],[70,22],[76,28],[78,28],[80,22],[78,16],[76,10],[74,8],[72,10],[68,14],[64,18],[62,24]],LAND);

  // Southeast Asia peninsula
  land([[100,20],[104,20],[108,18],[110,14],[108,10],[106,6],[104,2],[102,2],[100,6],[98,14],[100,20]],LAND);

  // Borneo
  land([[108,2],[118,4],[118,0],[112,-4],[108,-2],[108,2]],'rgba(26,61,107,0.85)');

  // Sumatra
  land([[96,5],[104,4],[106,2],[106,-4],[100,-4],[96,2],[96,5]],'rgba(26,61,107,0.85)');

  // Java
  land([[106,-6],[112,-6],[114,-8],[108,-8],[106,-6]],'rgba(26,61,107,0.85)');

  // AUSTRALIA
  land([[114,-22],[118,-18],[122,-16],[126,-14],[128,-12],[132,-12],[136,-12],
        [138,-14],[140,-18],[142,-18],[146,-18],[148,-20],[150,-22],[152,-24],
        [152,-28],[150,-34],[148,-38],[144,-38],[140,-38],[136,-36],[132,-32],
        [128,-32],[124,-32],[120,-32],[116,-28],[114,-24],[114,-22]],LAND);
  outline([[114,-22],[118,-18],[128,-12],[136,-12],[142,-18],[150,-22],[152,-28],[150,-34],[144,-38],[136,-36],[128,-32],[120,-32],[114,-24],[114,-22]],STROKE,0.8);

  // New Zealand (north + south islands)
  land([[174,-38],[178,-38],[178,-40],[174,-40],[174,-38]],'rgba(26,61,107,0.8)');
  land([[168,-44],[172,-44],[172,-46],[170,-48],[167,-46],[168,-44]],'rgba(26,61,107,0.8)');

  // ANTARCTICA (simplified base)
  cx.fillStyle='rgba(20,50,90,0.5)';
  cx.fillRect(0,H*0.87,W,H*0.13);

  // ── USA — highlighted slightly brighter ──────────────────────────
  land([[-124,49],[-110,49],[-96,49],[-88,48],[-84,46],[-76,44],[-75,45],
        [-72,41],[-67,47],[-70,43],[-71,41],[-74,39],[-75,38],[-76,35],
        [-80,32],[-85,30],[-88,30],[-97,26],[-100,25],[-105,30],[-109,31],
        [-114,32],[-117,32],[-124,37],[-124,42],[-124,49]],'#22508a');
  outline([[-124,49],[-110,49],[-96,49],[-88,48],[-76,44],[-75,45],[-72,41],[-67,47],[-70,43],[-71,41],[-74,39],[-75,38],[-80,32],[-88,30],[-97,26],[-105,30],[-117,32],[-124,37],[-124,42],[-124,49]],'rgba(80,140,220,0.3)',1.0);

  // ── Graticule (lat/lon grid) ──────────────────────────────────────
  cx.strokeStyle='rgba(45,100,180,0.12)';cx.lineWidth=0.6;
  for(var lt=-80;lt<=80;lt+=20){var gy=(90-lt)/180*H;cx.beginPath();cx.moveTo(0,gy);cx.lineTo(W,gy);cx.stroke();}
  for(var ln=0;ln<360;ln+=20){var gx=ln/360*W;cx.beginPath();cx.moveTo(gx,0);cx.lineTo(gx,H);cx.stroke();}
  // Equator brighter
  cx.strokeStyle='rgba(45,100,180,0.25)';cx.lineWidth=0.8;
  var eq=(90/180)*H;cx.beginPath();cx.moveTo(0,eq);cx.lineTo(W,eq);cx.stroke();
  // Tropics
  cx.strokeStyle='rgba(245,158,11,0.1)';cx.lineWidth=0.6;
  [[23.5],[-23.5]].forEach(function(a){var y=(90-a)/180*H;cx.beginPath();cx.moveTo(0,y);cx.lineTo(W,y);cx.stroke();});

  // ── Battleground state markers ───────────────────────────────────
  if(showBattleground){
    BATTLEGROUNDS.forEach(function(s){
      var p=px(s.lon,s.lat);
      var col=TC[s.type]||'#f59e0b';
      var rgb=s.type==='swing'?'245,158,11':s.type==='lean-r'?'220,38,38':'29,78,216';
      // Glow
      var rg=cx.createRadialGradient(p[0],p[1],0,p[0],p[1],26);
      rg.addColorStop(0,'rgba('+rgb+',0.85)');
      rg.addColorStop(0.45,'rgba('+rgb+',0.25)');
      rg.addColorStop(1,'transparent');
      cx.fillStyle=rg;cx.fillRect(p[0]-28,p[1]-28,56,56);
      // Dot
      cx.beginPath();cx.arc(p[0],p[1],3,0,Math.PI*2);cx.fillStyle='rgba(255,255,255,0.95)';cx.fill();
      // Ring
      cx.beginPath();cx.arc(p[0],p[1],6,0,Math.PI*2);cx.strokeStyle='rgba(255,255,255,0.4)';cx.lineWidth=0.8;cx.stroke();
      // Label
      cx.fillStyle='rgba(255,255,255,0.75)';cx.font='bold 11px monospace';cx.textAlign='center';
      cx.fillText(s.abbr,p[0],p[1]-10);
    });
  }

  return tc;
}

// ════════════════════════════════════════════════════════════════════
// Graphics engine — Canvas 2D
// ════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════
// GRAPHICS ENGINE — Pure Canvas 2D. Runs synchronously. Zero deps.
// Draws both: (1) Battleground mini-map, (2) Full 50-state explorer
// ═══════════════════════════════════════════════════════════════════

// State paths: D3 Albers USA layout, viewBox 960×600
// ═══════════════════════════════════════════════════════════════════
// VOTERLENS GRAPHICS ENGINE v3 — Production Grade
// Three modules: (1) Hero Globe  (2) Battleground Map  (3) USA Explorer
// All Canvas 2D — no WebGL/Three.js dependency issues
// Boots on window.load with dimension guards
// ═══════════════════════════════════════════════════════════════════

// ── SHARED: US State path data (D3 Albers USA, 960×600 viewBox) ────
var US_PATHS = {
  WA:[[124,67],[180,67],[180,97],[174,110],[158,118],[145,116],[132,115],[118,118],[108,121],[105,112],[124,67]],
  OR:[[105,112],[118,118],[132,115],[145,116],[158,118],[174,110],[180,97],[182,152],[164,165],[140,168],[105,168],[105,148]],
  CA:[[105,148],[105,168],[140,168],[164,165],[182,152],[186,198],[177,232],[167,265],[152,280],[134,270],[114,244],[106,216]],
  NV:[[152,108],[182,97],[215,112],[219,155],[202,180],[186,198],[177,232],[167,265],[160,198],[172,112]],
  ID:[[180,67],[232,67],[242,120],[225,140],[215,112],[182,97],[180,67]],
  MT:[[180,67],[322,67],[330,94],[309,106],[278,109],[242,120],[232,67],[180,67]],
  WY:[[215,112],[242,120],[330,94],[338,130],[332,156],[215,156]],
  UT:[[202,156],[219,155],[215,112],[172,112],[167,265],[202,232],[219,232],[222,196]],
  CO:[[215,156],[332,156],[339,186],[215,186]],
  AZ:[[167,265],[202,263],[222,263],[222,312],[202,332],[185,337],[163,322],[154,298]],
  NM:[[215,186],[339,186],[345,226],[283,260],[222,265],[219,232]],
  ND:[[278,67],[409,67],[418,85],[400,100],[330,94],[278,67]],
  SD:[[278,109],[330,94],[400,100],[409,120],[405,140],[278,140]],
  NE:[[278,140],[405,140],[409,160],[409,176],[330,176],[278,170]],
  KS:[[278,176],[409,176],[418,196],[418,212],[278,212]],
  OK:[[278,212],[418,212],[426,238],[390,254],[320,254],[278,238]],
  TX:[[278,238],[320,254],[390,254],[426,238],[446,274],[456,312],[450,360],[416,390],[370,396],[330,386],[300,360],[274,320],[258,292],[255,266]],
  MN:[[400,67],[498,67],[508,90],[503,115],[478,130],[428,130],[409,120],[400,100]],
  IA:[[409,130],[478,130],[503,115],[519,135],[514,160],[409,160]],
  MO:[[409,160],[514,160],[519,180],[519,206],[499,226],[476,231],[450,236],[426,220],[418,212],[418,196],[409,176],[409,160]],
  AR:[[426,236],[499,230],[519,236],[522,266],[499,281],[450,281],[426,266]],
  LA:[[426,281],[450,281],[499,281],[522,281],[525,301],[509,312],[489,327],[465,332],[440,317],[426,301]],
  WI:[[478,67],[550,67],[566,90],[556,115],[540,130],[503,115],[498,67]],
  MI:[[540,65],[598,65],[608,86],[598,106],[578,115],[559,108],[548,90]],
  IL:[[503,115],[540,130],[556,145],[550,176],[540,210],[519,226],[519,206],[519,180],[519,160],[519,135]],
  IN:[[556,145],[591,145],[600,176],[590,210],[570,220],[556,206],[550,176]],
  OH:[[591,120],[638,120],[652,151],[648,186],[628,200],[600,195],[590,210],[600,176],[591,145]],
  KY:[[519,226],[570,220],[590,210],[628,200],[648,216],[643,236],[612,251],[576,256],[550,251],[519,241]],
  TN:[[519,241],[550,251],[576,256],[612,251],[652,246],[672,261],[648,276],[590,276],[519,271]],
  MS:[[499,281],[522,266],[522,281],[525,301],[519,336],[499,347],[479,332],[464,296]],
  AL:[[499,281],[464,296],[479,332],[499,347],[519,351],[535,321],[539,291],[519,281]],
  GA:[[539,266],[590,266],[612,251],[652,246],[662,271],[652,312],[628,332],[590,336],[570,321],[550,296]],
  FL:[[550,336],[570,321],[590,336],[628,332],[652,352],[662,372],[653,402],[632,417],[612,422],[590,417],[571,402],[561,387],[555,366]],
  SC:[[612,251],[652,246],[672,261],[672,291],[652,312],[628,332],[612,312],[612,281]],
  NC:[[590,231],[648,216],[682,226],[707,241],[712,261],[672,261],[652,246],[612,251],[590,241]],
  VA:[[590,201],[648,201],[682,211],[707,201],[728,216],[712,236],[712,261],[707,241],[682,226],[648,216],[590,231]],
  WV:[[590,176],[648,176],[662,196],[652,216],[628,220],[612,211],[590,201]],
  PA:[[590,146],[692,146],[707,161],[707,181],[692,191],[648,186],[638,120],[591,120]],
  NY:[[590,106],[660,101],[707,101],[732,116],[728,141],[707,146],[707,161],[692,146],[590,146],[590,120]],
  VT:[[707,67],[740,67],[745,95],[732,116],[707,101]],
  NH:[[740,67],[765,67],[770,91],[760,116],[745,116],[732,116],[745,95]],
  ME:[[765,67],[813,67],[823,81],[812,106],[788,116],[765,101],[770,91]],
  MA:[[707,101],[745,101],[765,101],[770,116],[750,126],[732,126],[707,111]],
  RI:[[770,116],[786,116],[786,131],[770,131]],
  CT:[[732,126],[757,121],[770,131],[760,143],[732,138]],
  NJ:[[728,141],[752,136],[762,151],[752,166],[732,166],[728,151]],
  DE:[[745,156],[760,151],[765,166],[750,176],[742,166]],
  MD:[[707,161],[745,156],[745,166],[750,176],[730,186],[712,181],[707,166]],
  DC:[[718,172],[726,167],[726,175],[718,175]],
  AK:[[28,392],[158,392],[178,442],[166,478],[122,494],[72,490],[28,464]],
  HI:[[250,460],[284,460],[289,480],[273,490],[250,485]]
};

var US_LABELS = {
  WA:[141,98],  OR:[138,146], CA:[130,220], NV:[187,175], ID:[208,108],
  MT:[252,89],  WY:[271,130], UT:[198,196], CO:[274,170], AZ:[190,297],
  NM:[270,225], ND:[346,84],  SD:[346,120], NE:[346,158], KS:[348,194],
  OK:[350,228], TX:[352,316], MN:[452,100], IA:[458,145], MO:[464,195],
  AR:[466,256], LA:[468,304], WI:[524,100], MI:[564,89],  IL:[528,176],
  IN:[568,181], OH:[610,165], KY:[578,235], TN:[582,259], MS:[492,313],
  AL:[496,316], GA:[590,294], FL:[598,380], SC:[636,280], NC:[640,251],
  VA:[650,223], WV:[620,196], PA:[640,165], NY:[638,128], VT:[718,86],
  NH:[748,94],  ME:[785,90],  MA:[732,114], RI:[778,122], CT:[740,132],
  NJ:[736,152], DE:[752,160], MD:[722,171], DC:[722,170],
  AK:[102,443], HI:[272,475]
};

// Per-state distinct color palette — matches reference image style
// Each state has a unique vibrant fill + darker shade for 3D side
var STATE_COLORS = {
  WA: {fill:'#2196F3', side:'#0d6ebd'},  // blue
  OR: {fill:'#FF9800', side:'#c96d00'},  // orange
  CA: {fill:'#E91E63', side:'#a0134a'},  // pink/magenta
  NV: {fill:'#9E9E9E', side:'#616161'},  // grey
  ID: {fill:'#FF9800', side:'#c96d00'},  // orange
  MT: {fill:'#FFFFFF', side:'#bdbdbd'},  // white
  WY: {fill:'#9C27B0', side:'#6a0f80'},  // purple
  UT: {fill:'#03A9F4', side:'#0176a8'},  // light blue
  CO: {fill:'#4CAF50', side:'#2e7031'},  // green
  AZ: {fill:'#9E9E9E', side:'#616161'},  // grey
  NM: {fill:'#FFEB3B', side:'#c9b800'},  // yellow
  ND: {fill:'#03BCD4', side:'#017a88'},  // cyan
  SD: {fill:'#FF9800', side:'#c96d00'},  // orange
  NE: {fill:'#F44336', side:'#b71c1c'},  // red (Nebraska — like reference)
  KS: {fill:'#FFC107', side:'#c68a00'},  // amber
  OK: {fill:'#FF9800', side:'#c96d00'},  // orange (darker)
  TX: {fill:'#FFEB3B', side:'#c9b800'},  // yellow
  MN: {fill:'#03A9F4', side:'#0176a8'},  // light blue
  IA: {fill:'#FFFFFF', side:'#bdbdbd'},  // white
  MO: {fill:'#03BCD4', side:'#017a88'},  // cyan
  AR: {fill:'#CDDC39', side:'#8a9600'},  // lime
  LA: {fill:'#9C27B0', side:'#6a0f80'},  // purple
  WI: {fill:'#FFC107', side:'#c68a00'},  // amber
  MI: {fill:'#4CAF50', side:'#2e7031'},  // green
  IL: {fill:'#03BCD4', side:'#017a88'},  // cyan
  IN: {fill:'#FF5722', side:'#bf360c'},  // deep orange
  OH: {fill:'#9E9E9E', side:'#616161'},  // grey
  KY: {fill:'#FF9800', side:'#c96d00'},  // orange
  TN: {fill:'#FF9800', side:'#c96d00'},  // orange (diff shade)
  MS: {fill:'#9C27B0', side:'#6a0f80'},  // purple
  AL: {fill:'#F44336', side:'#b71c1c'},  // red
  GA: {fill:'#FFEB3B', side:'#c9b800'},  // yellow
  FL: {fill:'#FF5722', side:'#bf360c'},  // deep orange
  SC: {fill:'#03BCD4', side:'#017a88'},  // cyan
  NC: {fill:'#8BC34A', side:'#558b2f'},  // light green
  VA: {fill:'#FF9800', side:'#c96d00'},  // orange
  WV: {fill:'#CDDC39', side:'#8a9600'},  // lime
  PA: {fill:'#FFC107', side:'#c68a00'},  // amber
  NY: {fill:'#03A9F4', side:'#0176a8'},  // light blue
  VT: {fill:'#4CAF50', side:'#2e7031'},  // green
  NH: {fill:'#FF9800', side:'#c96d00'},  // orange
  ME: {fill:'#2196F3', side:'#0d6ebd'},  // blue
  MA: {fill:'#9C27B0', side:'#6a0f80'},  // purple
  RI: {fill:'#F44336', side:'#b71c1c'},  // red
  CT: {fill:'#03BCD4', side:'#017a88'},  // cyan
  NJ: {fill:'#FF5722', side:'#bf360c'},  // deep orange
  DE: {fill:'#4CAF50', side:'#2e7031'},  // green
  MD: {fill:'#F44336', side:'#b71c1c'},  // red
  DC: {fill:'#212121', side:'#000000'},  // near-black
  AK: {fill:'#03BCD4', side:'#017a88'},  // cyan
  HI: {fill:'#4CAF50', side:'#2e7031'},  // green
};

// Fallback lean colors (not used if STATE_COLORS has entry)
var LEAN_FILL = {
  'solid-r':'#F44336','lean-r':'#FF5722',
  'swing':  '#FFC107',
  'lean-b': '#2196F3','solid-b':'#1565C0'
};
var LEAN_SIDE = {
  'solid-r':'#b71c1c','lean-r':'#bf360c',
  'swing':  '#c68a00',
  'lean-b': '#0d6ebd','solid-b':'#0d3b76'
};

// Battleground state data
// Battleground state data
var BG_SET  = {PA:1,MI:1,WI:1,AZ:1,NV:1,GA:1,NC:1,FL:1,TX:1,MN:1,NH:1,VA:1};
var BG_TYPE = {PA:'swing',MI:'swing',WI:'swing',AZ:'swing',NV:'swing',GA:'swing',
               NC:'lean-r',FL:'lean-r',TX:'lean-r',MN:'lean-b',NH:'lean-b',VA:'lean-b'};
var BG_COLOR = {swing:'#d97706','lean-r':'#dc2626','lean-b':'#2563eb'};

// ── SHARED: build Path2D objects from US_PATHS coordinates ─────────
function buildStatePaths(scale, ox, oy) {
  var paths = {};
  var keys = Object.keys(US_PATHS);
  for (var i = 0; i < keys.length; i++) {
    var abbr = keys[i];
    var pts  = US_PATHS[abbr];
    var p    = new Path2D();
    for (var j = 0; j < pts.length; j++) {
      var x = ox + pts[j][0] * scale;
      var y = oy + pts[j][1] * scale;
      j === 0 ? p.moveTo(x, y) : p.lineTo(x, y);
    }
    p.closePath();
    paths[abbr] = p;
  }
  return paths;
}

function calcMapTransform(W, H, padFrac) {
  var pad  = padFrac === undefined ? 0.04 : padFrac;
  var scl  = Math.min(W * (1 - pad * 2) / 960, H * (1 - pad * 2) / 600);
  var ox   = (W - 960 * scl) / 2;
  var oy   = (H - 600 * scl) / 2;
  return { scale: scl, ox: ox, oy: oy };
}

// Lean label helpers (shared by both maps)
function leanLabel(l) {
  return {swing:'Battleground / Swing','lean-r':'Leans Republican','lean-b':'Leans Democrat',
          'solid-r':'Safe Republican','solid-b':'Safe Democrat'}[l] || l;
}
function leanCls(l) {
  return {swing:'tt-swing','lean-r':'tt-lean-r','lean-b':'tt-lean-b',
          'solid-r':'tt-solid-r','solid-b':'tt-solid-b'}[l] || 'tt-swing';
}

// ═══════════════════════════════════════════════════════════════════
// MODULE 1 — HERO GLOBE (canvas id="globe-c")
// Simple, smooth, elegant rotating globe with continents.
// Pure Canvas 2D. No Three.js. Smooth 60fps rotation.
// ═══════════════════════════════════════════════════════════════════
var _heroGlobe = null;

function initHeroGlobe() {
  var canvas = document.getElementById('globe-c');
  if (!canvas || canvas._built) return;
  canvas._built = true;

  var wrap = canvas.parentElement;
  var W = wrap.offsetWidth || 500;
  var H = wrap.offsetHeight || 500;
  canvas.width  = W * (window.devicePixelRatio || 1);
  canvas.height = H * (window.devicePixelRatio || 1);
  canvas.style.width  = W + 'px';
  canvas.style.height = H + 'px';

  var ctx = canvas.getContext('2d');
  if (!ctx) return;
  var dpr = window.devicePixelRatio || 1;
  ctx.scale(dpr, dpr);

  var R    = Math.min(W, H) * 0.44;
  var cx2  = W / 2, cy2 = H / 2;
  var lon0 = -1.68; // rads — centers USA
  var rotY = lon0;
  var raf  = null;
  var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var dragging=false,lastGX=0,hoverBoost=0;
  function isLight(){return document.documentElement.getAttribute('data-theme')==='light';}
  canvas.addEventListener('pointerdown',function(e){dragging=true;lastGX=e.clientX;canvas.setPointerCapture&&canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',function(e){hoverBoost=1;if(dragging){rotY+=(e.clientX-lastGX)*0.006;lastGX=e.clientX;}});
  canvas.addEventListener('pointerup',function(e){dragging=false;canvas.releasePointerCapture&&canvas.releasePointerCapture(e.pointerId);});
  canvas.addEventListener('pointerleave',function(){dragging=false;hoverBoost=0;});

  // World landmass polygons [lon_deg, lat_deg] pairs
  var LANDS = [
    // North America
    [[-168,72],[-162,70],[-150,60],[-130,55],[-125,50],[-124,48],[-110,49],[-96,49],[-85,48],
     [-75,45],[-72,41],[-67,47],[-70,43],[-74,39],[-76,35],[-80,32],[-88,30],[-97,26],
     [-105,30],[-117,32],[-124,37],[-124,49],[-130,55],[-142,60],[-168,66]],
    // Greenland
    [[-56,83],[-28,84],[-14,78],[-22,72],[-44,70],[-58,78]],
    // South America
    [[-80,12],[-72,12],[-52,5],[-50,2],[-44,-3],[-38,-10],[-36,-22],[-44,-23],
     [-52,-33],[-62,-42],[-68,-55],[-72,-38],[-70,-18],[-80,-5]],
    // Europe
    [[-10,38],[0,38],[8,44],[16,40],[22,38],[28,42],[36,48],[28,52],[18,60],[8,56],[2,52],[-4,48],[-8,44]],
    // Scandinavia
    [[4,58],[10,57],[18,58],[26,64],[28,68],[22,70],[16,68],[10,62]],
    // Africa
    [[-18,16],[-8,12],[0,10],[8,4],[14,8],[22,10],[32,10],[40,12],[44,4],[40,-4],
     [34,-18],[28,-34],[22,-36],[16,-28],[8,-20],[0,-4],[-8,4],[-16,12]],
    // Asia
    [[36,42],[44,38],[52,28],[60,24],[70,22],[80,26],[88,28],[96,22],[108,20],[118,24],
     [130,36],[138,44],[140,48],[130,60],[100,72],[68,78],[44,68],[36,60],[28,46],[32,42]],
    // Australia
    [[114,-22],[122,-16],[130,-12],[138,-14],[142,-18],[150,-22],[152,-28],[150,-34],
     [144,-38],[136,-36],[128,-32],[120,-32],[114,-24]],
    // Indian subcontinent
    [[62,24],[70,22],[76,28],[80,22],[78,16],[74,8],[72,10],[66,18]],
    // UK
    [[-6,50],[0,52],[2,52],[-2,54],[-6,58],[-8,54]],
  ];

  // USA brighter highlight
  var USA_POLY = [[-124,49],[-110,49],[-96,49],[-85,48],[-75,45],[-72,41],[-67,47],[-70,43],
                  [-74,39],[-76,35],[-80,32],[-88,30],[-97,26],[-105,30],[-117,32],[-124,37],[-124,49]];

  function ll2xyz(lon_rad, lat_deg) {
    // Convert lon/lat to 3D unit sphere
    var phi = (90 - lat_deg) * Math.PI / 180;
    var lam = lon_rad;
    return {
      x: Math.sin(phi) * Math.cos(lam),
      y: Math.cos(phi),
      z: Math.sin(phi) * Math.sin(lam)
    };
  }

  function project(lon_deg, lat_deg, rot) {
    // Project lat/lon to canvas 2D given current globe rotation
    var lam = lon_deg * Math.PI / 180 + rot;
    var v   = ll2xyz(lam, lat_deg);
    // Orthographic projection — only draw front hemisphere
    if (v.z < 0) return null;
    return {
      x: cx2 + v.x * R,
      y: cy2 - v.y * R,
      vis: v.z  // visibility (0=edge, 1=center)
    };
  }

  function drawPoly(pts, fill, stroke, sw) {
    var started = false;
    ctx.beginPath();
    for (var i = 0; i < pts.length; i++) {
      var p = project(pts[i][0], pts[i][1], rotY);
      if (!p) { started = false; continue; }
      if (!started) { ctx.moveTo(p.x, p.y); started = true; }
      else ctx.lineTo(p.x, p.y);
    }
    if (!started) return;
    ctx.closePath();
    if (fill)   { ctx.fillStyle   = fill; ctx.fill(); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = sw || 0.5; ctx.stroke(); }
  }

  function frame() {
    ctx.clearRect(0, 0, W, H);

    // Ocean sphere
    var grad = ctx.createRadialGradient(cx2 - R*0.25, cy2 - R*0.25, R*0.05, cx2, cy2, R);
    if(isLight()){grad.addColorStop(0,'#dbeafe');grad.addColorStop(0.48,'#93c5fd');grad.addColorStop(1,'#1e3a8a');}else{grad.addColorStop(0, '#0f2240');grad.addColorStop(0.5,'#071628');grad.addColorStop(1, '#020c1a');}
    ctx.beginPath();
    ctx.arc(cx2, cy2, R, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Atmosphere rim
    var atmGrad = ctx.createRadialGradient(cx2, cy2, R * 0.96, cx2, cy2, R * 1.08);
    atmGrad.addColorStop(0,   'rgba(30,80,180,0.0)');
    atmGrad.addColorStop(0.5, 'rgba(30,80,180,0.2)');
    atmGrad.addColorStop(1,   'rgba(30,80,180,0.0)');
    ctx.beginPath();
    ctx.arc(cx2, cy2, R * 1.08, 0, Math.PI * 2);
    ctx.fillStyle = atmGrad;
    ctx.fill();

    // Clip to sphere
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx2, cy2, R, 0, Math.PI * 2);
    ctx.clip();

    // Graticule
    ctx.strokeStyle = 'rgba(40,90,160,0.15)';
    ctx.lineWidth   = 0.4;
    for (var lat = -80; lat <= 80; lat += 20) {
      var pts_lat = [];
      for (var lon = -180; lon <= 180; lon += 3) pts_lat.push([lon, lat]);
      drawPoly(pts_lat, null, 'rgba(40,90,160,0.15)', 0.4);
    }
    for (var lon2 = -180; lon2 <= 180; lon2 += 20) {
      var pts_lon = [];
      for (var lat2 = -85; lat2 <= 85; lat2 += 3) pts_lon.push([lon2, lat2]);
      drawPoly(pts_lon, null, 'rgba(40,90,160,0.15)', 0.4);
    }

    // Landmasses
    for (var li = 0; li < LANDS.length; li++) {
      drawPoly(LANDS[li], isLight() ? '#f8fafc' : '#1a3d6e', isLight() ? 'rgba(30,64,175,0.35)' : 'rgba(30,80,150,0.3)', 0.55);
    }
    // USA highlight
    drawPoly(USA_POLY, isLight() ? '#dc2626' : '#60a5fa', isLight() ? 'rgba(185,28,28,0.9)' : 'rgba(147,197,253,0.95)', 1.8 + hoverBoost*0.7);
    if(hoverBoost){drawPoly(USA_POLY, 'rgba(245,158,11,0.18)', 'rgba(245,158,11,0.75)', 2.4);}

    ctx.restore();

    // Subtle outer glow
    var glowGrad = ctx.createRadialGradient(cx2, cy2, R * 0.9, cx2, cy2, R * 1.15);
    glowGrad.addColorStop(0,   'rgba(29,78,216,0.0)');
    glowGrad.addColorStop(0.6, 'rgba(29,78,216,0.08)');
    glowGrad.addColorStop(1,   'rgba(29,78,216,0.0)');
    ctx.beginPath();
    ctx.arc(cx2, cy2, R * 1.15, 0, Math.PI * 2);
    ctx.fillStyle = glowGrad;
    ctx.fill();

    // Specular highlight
    var specGrad = ctx.createRadialGradient(cx2 - R*0.3, cy2 - R*0.3, 0, cx2 - R*0.1, cy2 - R*0.1, R*0.65);
    specGrad.addColorStop(0,   'rgba(180,210,255,0.12)');
    specGrad.addColorStop(1,   'rgba(180,210,255,0.0)');
    ctx.beginPath();
    ctx.arc(cx2, cy2, R, 0, Math.PI * 2);
    ctx.fillStyle = specGrad;
    ctx.fill();

    if (!prefersReduced && !dragging) rotY += 0.0018 + hoverBoost*0.0008; // slow, smooth rotation
  }

  function loop() { frame(); raf = requestAnimationFrame(loop); }
  loop();
  _heroGlobe = { raf: raf, canvas: canvas };

  // Resize
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      var NW = wrap.offsetWidth || 500;
      var NH = wrap.offsetHeight || 500;
      W = NW; H = NH;
      canvas.width  = NW * dpr; canvas.height = NH * dpr;
      canvas.style.width = NW + 'px'; canvas.style.height = NH + 'px';
      ctx.scale(dpr, dpr);
      R = Math.min(W, H) * 0.44; cx2 = W / 2; cy2 = H / 2;
    }, 200);
  });
}

// ═══════════════════════════════════════════════════════════════════
// MODULE 2 — BATTLEGROUND MAP (canvas id="bg-map-canvas")
// US map, non-battleground states faded, battleground states lit
// with animated pulsing dots. Clean and tactical.
// ═══════════════════════════════════════════════════════════════════
function initBattlegroundMap() {
  var canvas = document.getElementById('bg-map-canvas');
  if (!canvas || canvas._built) return;
  canvas._built = true;

  var wrap  = canvas.parentElement;
  var dpr   = Math.min(window.devicePixelRatio || 1, 2);
  var W     = wrap.offsetWidth  || 560;
  var H     = wrap.offsetHeight || 400;

  canvas.width  = W * dpr;
  canvas.height = H * dpr;
  canvas.style.width  = W + 'px';
  canvas.style.height = H + 'px';

  var ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var tick = 0;

  function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = 'rgba(2,8,22,0.6)';
    ctx.fillRect(0, 0, W, H);

    var t    = calcMapTransform(W, H, 0.04);
    var scl  = t.scale, ox = t.ox, oy = t.oy;
    var paths = buildStatePaths(scl, ox, oy);

    // Draw all states — faded if not battleground
    var keys = Object.keys(US_PATHS);
    for (var i = 0; i < keys.length; i++) {
      var abbr = keys[i];
      var isBG = !!BG_SET[abbr];
      var p    = paths[abbr];
      if (!p) continue;

      if (isBG) {
        var typ  = BG_TYPE[abbr];
        var fill = BG_COLOR[typ] || '#d97706';
        // Slightly darken for side effect
        ctx.save();
        ctx.translate(scl * 0.6, -scl * 0.8);
        ctx.fillStyle = '#000';
        ctx.globalAlpha = 0.4;
        ctx.fill(p);
        ctx.restore();
        ctx.fillStyle     = fill;
        ctx.globalAlpha   = 1;
        ctx.fill(p);
        ctx.strokeStyle   = 'rgba(3,7,15,0.7)';
        ctx.lineWidth     = Math.max(0.5, scl * 0.35);
        ctx.stroke(p);
        // Bright border
        ctx.strokeStyle = fill.replace(')', ',0.6)').replace('rgb','rgba');
        ctx.lineWidth   = Math.max(1, scl * 0.5);
        ctx.stroke(p);
      } else {
        ctx.fillStyle   = '#0e1f3a';
        ctx.globalAlpha = 0.7;
        ctx.fill(p);
        ctx.strokeStyle = 'rgba(3,7,15,0.5)';
        ctx.lineWidth   = Math.max(0.3, scl * 0.3);
        ctx.globalAlpha = 1;
        ctx.stroke(p);
      }
    }

    // Battleground labels + pulse dots
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    var bgKeys = Object.keys(BG_SET);
    for (var bi = 0; bi < bgKeys.length; bi++) {
      var ab   = bgKeys[bi];
      var lp   = US_LABELS[ab]; if (!lp) continue;
      var lx   = ox + lp[0] * scl;
      var ly   = oy + lp[1] * scl;
      var typ2 = BG_TYPE[ab];
      var col  = BG_COLOR[typ2] || '#d97706';

      // Pulsing ring
      var pulse = prefersReduced ? 0.7 : (0.5 + 0.5 * Math.sin(tick + bi * 0.8));
      var rad   = Math.max(4, scl * 5) * (0.85 + 0.3 * pulse);
      ctx.beginPath();
      ctx.arc(lx, ly, rad, 0, Math.PI * 2);
      ctx.strokeStyle = col;
      ctx.globalAlpha = 0.25 + 0.25 * pulse;
      ctx.lineWidth   = Math.max(1, scl * 1.2);
      ctx.stroke();

      // Core dot
      ctx.beginPath();
      ctx.arc(lx, ly, Math.max(2.5, scl * 2.8), 0, Math.PI * 2);
      ctx.fillStyle   = '#fff';
      ctx.globalAlpha = 0.95;
      ctx.fill();

      // Label
      var fs = Math.min(Math.max(8, scl * 11), 12);
      ctx.font        = 'bold ' + fs + 'px "JetBrains Mono",monospace';
      ctx.fillStyle   = 'rgba(0,0,0,0.9)';
      ctx.globalAlpha = 1;
      ctx.fillText(ab, lx + 0.7, ly + 0.7);
      ctx.fillStyle = '#fff';
      ctx.fillText(ab, lx, ly);
    }

    ctx.globalAlpha = 1;
    if (!prefersReduced) tick += 0.03;
  }

  draw();
  if (!prefersReduced) {
    (function loop() { draw(); requestAnimationFrame(loop); })();
  }

  // Responsive resize — debounced
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      var NW = wrap.offsetWidth || 560;
      var NH = wrap.offsetHeight || 400;
      W = NW; H = NH;
      canvas.width  = NW * dpr; canvas.height = NH * dpr;
      canvas.style.width  = NW + 'px'; canvas.style.height = NH + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      draw();
    }, 200);
  });
}

// ═══════════════════════════════════════════════════════════════════
// MODULE 3 — 3D ROTATING USA MAP EXPLORER
// Three.js loaded async. States extruded as 3D geometry.
// Drag to rotate, scroll to zoom, click states to open chat.
// Falls back to Canvas 2D if Three.js fails to load.
// ═══════════════════════════════════════════════════════════════════
function initExplorerMap() {
  var canvas = document.getElementById('map-canvas');
  if (!canvas || canvas._built) return;
  canvas._built = true;

  var stage = canvas.parentElement;

  // Load Three.js then build 3D map
  var s = document.createElement('script');
  s.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
  s.onload  = function() { build3DMap(canvas, stage); };
  s.onerror = function() { build2DFallback(canvas, stage); };
  document.head.appendChild(s);
}

function build3DMap(canvas, stage) {
  if (!window.THREE) { build2DFallback(canvas, stage); return; }

  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var W   = stage.offsetWidth  || Math.min(window.innerWidth - 40, 1100);
  var H   = stage.offsetHeight || 500;

  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
  renderer.setSize(W, H);
  renderer.setPixelRatio(dpr);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type    = THREE.PCFSoftShadowMap;
  renderer.setClearColor(0x0a1628, 1);

  var scene  = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(35, W / H, 0.1, 1000);
  camera.position.set(0, 8, 14);
  camera.lookAt(0, 0.5, 0);

  // ── Lighting ────────────────────────────────────────────────────
  scene.add(new THREE.AmbientLight(0xffffff, 0.9));
  var sun = new THREE.DirectionalLight(0xffffff, 1.8);
  sun.position.set(8, 14, 10);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.near = 0.5;
  sun.shadow.camera.far  = 60;
  sun.shadow.camera.left = sun.shadow.camera.bottom = -14;
  sun.shadow.camera.right = sun.shadow.camera.top   =  14;
  scene.add(sun);
  var fill = new THREE.DirectionalLight(0x8aadff, 0.6);
  fill.position.set(-8, 4, -6);
  scene.add(fill);

  // ── Base platform ───────────────────────────────────────────────
  var plat = new THREE.Mesh(
    new THREE.BoxGeometry(18, 0.12, 13),
    new THREE.MeshPhongMaterial({ color: 0x040d1e, shininess: 8 })
  );
  plat.position.y = -0.18;
  plat.receiveShadow = true;
  scene.add(plat);

  // Ocean surface
  var ocean = new THREE.Mesh(
    new THREE.PlaneGeometry(22, 16),
    new THREE.MeshPhongMaterial({ color: 0x071628, shininess: 40, specular: new THREE.Color(0.04, 0.08, 0.18) })
  );
  ocean.rotation.x = -Math.PI / 2;
  ocean.position.y = -0.12;
  ocean.receiveShadow = true;
  scene.add(ocean);

  // ── Project state paths into 3D ─────────────────────────────────
  var VW = 960, VH = 600;
  var MAP_W = 16.5, MAP_H = 10.5;
  var OX = -MAP_W / 2, OY = -MAP_H / 2;
  var EH = 0.40;

  var COLORS = {
    'solid-r':'#b91c1c','lean-r':'#dc2626','swing':'#d97706','lean-b':'#2563eb','solid-b':'#1d4ed8'
  };
  var COLORS_DARK = {
    'solid-r':'#7f1d1d','lean-r':'#991b1b','swing':'#78350f','lean-b':'#1e3a8a','solid-b':'#1e3a8a'
  };

  function hexToColor(h) { return new THREE.Color(parseInt(h.replace('#',''),16)/0xFFFFFF*0xFFFFFF|0).setStyle(h); }

  var stateMeshes  = {};
  var meshToAbbr   = new Map();
  var allMeshes    = [];
  var labelMeshes  = [];
  var hoveredMesh  = null;
  var hoveredAbbr  = null;

  function px2w(sx, sy) {
    return [OX + (sx / VW) * MAP_W, OY + (sy / VH) * MAP_H];
  }

  // Build state meshes
  Object.keys(US_PATHS).forEach(function(abbr) {
    var pts  = US_PATHS[abbr];
    var data = MAP_STATE_DATA ? MAP_STATE_DATA[abbr] : null;
    var lean = data ? data.lean : 'solid-b';

    // Centroid for gap shrink
    var cx3 = pts.reduce(function(a,p){return a+p[0];},0) / pts.length;
    var cy3 = pts.reduce(function(a,p){return a+p[1];},0) / pts.length;

    var shape = new THREE.Shape();
    pts.forEach(function(p, i) {
      var gx = 0.008, shrinkX = cx3 + (p[0]-cx3)*(1-gx);
      var gy = 0.008, shrinkY = cy3 + (p[1]-cy3)*(1-gy);
      var w = px2w(shrinkX, shrinkY);
      i === 0 ? shape.moveTo(w[0], w[1]) : shape.lineTo(w[0], w[1]);
    });
    shape.closePath();

    var geo = new THREE.ExtrudeGeometry(shape, {
      depth: EH, bevelEnabled: true,
      bevelThickness: 0.012, bevelSize: 0.012, bevelSegments: 2
    });

    var topC  = new THREE.Color(COLORS[lean]      || '#1d4ed8');
    var sideC = new THREE.Color(COLORS_DARK[lean] || '#1e3a8a');

    var topMat  = new THREE.MeshPhongMaterial({ color: topC,  shininess: 55, specular: new THREE.Color(0.1,0.1,0.15) });
    var sideMat = new THREE.MeshPhongMaterial({ color: sideC, shininess: 20 });

    var mesh = new THREE.Mesh(geo, [sideMat, topMat]);
    mesh.rotation.x  = -Math.PI / 2;
    mesh.position.y  = 0;
    mesh.castShadow  = true;
    mesh.receiveShadow = true;
    mesh.userData    = { abbr: abbr, lean: lean, origTop: topC.clone(), origSide: sideC.clone() };
    meshToAbbr.set(mesh, abbr);
    scene.add(mesh);
    stateMeshes[abbr] = mesh;
    allMeshes.push(mesh);

    // Label
    var lpos = US_LABELS[abbr];
    if (lpos) {
      var lw   = px2w(lpos[0], lpos[1]);
      var tiny = ['RI','DC','DE'].indexOf(abbr) >= 0;
      var small= ['CT','NJ','NH','VT','MA','MD','HI','WV'].indexOf(abbr) >= 0;
      var cw   = tiny ? 64 : small ? 80 : 112;
      var ch   = tiny ? 32 : small ? 40 : 52;
      var lc   = document.createElement('canvas');
      lc.width = cw; lc.height = ch;
      var lctx = lc.getContext('2d');
      lctx.fillStyle = 'rgba(0,0,0,0.35)';
      lctx.beginPath(); lctx.roundRect(2,2,cw-4,ch-4,4); lctx.fill();
      lctx.fillStyle = 'rgba(255,255,255,0.97)';
      lctx.font = 'bold '+(tiny?13:small?16:20)+'px "JetBrains Mono",monospace';
      lctx.textAlign = 'center'; lctx.textBaseline = 'middle';
      lctx.shadowColor='rgba(0,0,0,0.9)'; lctx.shadowBlur=4;
      lctx.fillText(abbr, cw/2, ch/2);
      var lmesh = new THREE.Mesh(
        new THREE.PlaneGeometry(tiny?0.5:small?0.65:0.9, tiny?0.25:small?0.32:0.42),
        new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(lc), transparent: true, depthWrite: false })
      );
      lmesh.position.set(lw[0], EH + 0.05, -lw[1]);
      lmesh.rotation.x = -Math.PI / 2;
      scene.add(lmesh);
      labelMeshes.push(lmesh);
    }
  });

  // ── Tooltip ─────────────────────────────────────────────────────
  var tooltip = document.getElementById('map-tooltip');
  var raycaster = new THREE.Raycaster();
  var mouse2d   = new THREE.Vector2();

  function getLeanLabel(l){return{swing:'Battleground / Swing','lean-r':'Leans Republican','lean-b':'Leans Democrat','solid-r':'Safe Republican','solid-b':'Safe Democrat'}[l]||l;}
  function getLeanCls(l){return{swing:'tt-swing','lean-r':'tt-lean-r','lean-b':'tt-lean-b','solid-r':'tt-solid-r','solid-b':'tt-solid-b'}[l]||'tt-swing';}

  function showTT(abbr, ex, ey) {
    var d = MAP_STATE_DATA ? MAP_STATE_DATA[abbr] : null;
    if (!d || !tooltip) return;
    tooltip.innerHTML =
      '<div class="tt-state">' + d.name + '</div>' +
      '<div class="tt-abbr">' + abbr + ' &middot; ' + d.ev + ' Electoral Votes</div>' +
      '<div class="tt-row"><span class="tt-icon">&#128203;</span><span>Registration: <span class="tt-val">' + d.reg + '</span></span></div>' +
      '<div class="tt-row"><span class="tt-icon">&#129306;</span><span>Voter ID: <span class="tt-val">' + d.id + '</span></span></div>' +
      '<div class="tt-row"><span class="tt-icon">&#128197;</span><span>Early voting: <span class="tt-val">' + d.early + '</span></span></div>' +
      '<div class="tt-row"><span class="tt-icon">&#9993;</span><span>Mail-in: <span class="tt-val">' + d.absentee + '</span></span></div>' +
      '<span class="tt-lean ' + getLeanCls(d.lean) + '">' + getLeanLabel(d.lean) + '</span>' +
      '<div class="tt-cta">Click to ask VoterLens &#8594;</div>';
    var sr = stage.getBoundingClientRect();
    var tx = ex - sr.left + 18, ty = ey - sr.top - 10;
    if (tx + 340 > W) tx = ex - sr.left - 355;
    if (ty < 10) ty = 10;
    tooltip.style.left = tx + 'px'; tooltip.style.top = ty + 'px';
    tooltip.classList.add('show');
  }
  function hideTT() { if (tooltip) tooltip.classList.remove('show'); }

  function doRaycast(e) {
    var r = canvas.getBoundingClientRect();
    mouse2d.x =  ((e.clientX - r.left) / r.width)  * 2 - 1;
    mouse2d.y = -((e.clientY - r.top)  / r.height) * 2 + 1;
    raycaster.setFromCamera(mouse2d, camera);
    return raycaster.intersectObjects(allMeshes);
  }

  function setHover(mesh, abbr) {
    if (abbr === hoveredAbbr) return;
    // un-hover old
    if (hoveredMesh && Array.isArray(hoveredMesh.material)) {
      hoveredMesh.material[0].color.copy(hoveredMesh.userData.origSide);
      hoveredMesh.material[1].color.copy(hoveredMesh.userData.origTop);
      hoveredMesh.material[0].emissive.set(0,0,0);
      hoveredMesh.material[1].emissive.set(0,0,0);
      hoveredMesh.position.y = 0;
    }
    hoveredAbbr = abbr; hoveredMesh = mesh;
    if (hoveredMesh && Array.isArray(hoveredMesh.material)) {
      hoveredMesh.material[1].color.set(0xdbeafe);
      hoveredMesh.material[0].color.set(0x6b9bbf);
      hoveredMesh.material[1].emissive.set(0.08, 0.12, 0.25);
      hoveredMesh.position.y = 0.15;
    }
  }
  function clearHover() {
    if (hoveredMesh && Array.isArray(hoveredMesh.material)) {
      hoveredMesh.material[0].color.copy(hoveredMesh.userData.origSide);
      hoveredMesh.material[1].color.copy(hoveredMesh.userData.origTop);
      hoveredMesh.material[0].emissive.set(0,0,0);
      hoveredMesh.material[1].emissive.set(0,0,0);
      hoveredMesh.position.y = 0;
    }
    hoveredMesh = null; hoveredAbbr = null;
  }

  // ── Orbit controls (manual, no dep) ─────────────────────────────
  var isDragging = false, lastX = 0, lastY = 0;
  var theta = 0, phi = 0.58, radius = 16.5;
  var autoRotate = false;
  var rotBtn = document.getElementById('mc-rotate');

  window.mapToggleRotate = function() { autoRotate = !autoRotate; if(rotBtn)rotBtn.classList.toggle('active',autoRotate); };
  window.mapReset = function() { theta=0; phi=0.58; radius=16.5; autoRotate=false; if(rotBtn)rotBtn.classList.remove('active'); clearHover(); };

  canvas.addEventListener('mousedown', function(e) {
    isDragging=true; lastX=e.clientX; lastY=e.clientY;
    autoRotate=false; if(rotBtn)rotBtn.classList.remove('active');
  });
  window.addEventListener('mouseup', function() { isDragging=false; });
  window.addEventListener('mousemove', function(e) {
    if (isDragging) {
      theta -= (e.clientX-lastX)*0.007;
      phi    = Math.max(0.15, Math.min(1.35, phi-(e.clientY-lastY)*0.005));
      lastX=e.clientX; lastY=e.clientY;
    }
  });
  canvas.addEventListener('wheel', function(e) {
    e.preventDefault(); radius = Math.max(6, Math.min(26, radius+e.deltaY*0.02));
  },{passive:false});

  // Hover + click events
  canvas.addEventListener('mousemove', function(e) {
    var hits = doRaycast(e);
    if (hits.length > 0) {
      var m    = hits[0].object;
      var abbr = meshToAbbr.get(m) || m.userData.abbr;
      if (abbr) { setHover(m, abbr); showTT(abbr, e.clientX, e.clientY); }
      canvas.style.cursor = 'pointer';
    } else {
      clearHover(); hideTT(); canvas.style.cursor = 'default';
    }
  });
  canvas.addEventListener('mouseleave', function() { clearHover(); hideTT(); canvas.style.cursor='default'; });

  canvas.addEventListener('click', function(e) {
    var hits = doRaycast(e);
    if (hits.length > 0) {
      var abbr = meshToAbbr.get(hits[0].object) || hits[0].object.userData.abbr;
      if (!abbr || !MAP_STATE_DATA || !MAP_STATE_DATA[abbr]) return;
      if(document.getElementById('home-state')) document.getElementById('home-state').value = abbr;
      if(document.getElementById('chat-state')) document.getElementById('chat-state').value = abbr;
      if (typeof window.showStateLocator === 'function') {
        window.showStateLocator(abbr);
      }
    }
  });

  // Touch
  var pTX=0,pTY=0,pDist=0;
  canvas.addEventListener('touchstart',function(e){if(e.touches.length===1){pTX=e.touches[0].clientX;pTY=e.touches[0].clientY;}if(e.touches.length===2){var dx=e.touches[0].clientX-e.touches[1].clientX,dy=e.touches[0].clientY-e.touches[1].clientY;pDist=Math.sqrt(dx*dx+dy*dy);}autoRotate=false;},{passive:true});
  canvas.addEventListener('touchmove',function(e){if(e.touches.length===1){theta-=(e.touches[0].clientX-pTX)*0.01;phi=Math.max(.15,Math.min(1.35,phi-(e.touches[0].clientY-pTY)*0.008));pTX=e.touches[0].clientX;pTY=e.touches[0].clientY;}if(e.touches.length===2){var dx=e.touches[0].clientX-e.touches[1].clientX,dy=e.touches[0].clientY-e.touches[1].clientY;var nd=Math.sqrt(dx*dx+dy*dy);radius=Math.max(6,Math.min(26,radius*(pDist/nd)));pDist=nd;}},{passive:true});

  // ── Render loop ──────────────────────────────────────────────────
  var tick = 0;
  function loop() {
    requestAnimationFrame(loop);
    tick += 0.01;
    if (autoRotate) theta += 0.004;

    camera.position.x = radius * Math.sin(phi) * Math.sin(theta);
    camera.position.y = radius * Math.cos(phi);
    camera.position.z = radius * Math.sin(phi) * Math.cos(theta);
    camera.lookAt(0, 0.5, 0);

    // Labels face camera
    labelMeshes.forEach(function(lm) {
      lm.quaternion.copy(camera.quaternion);
      lm.rotation.x = -Math.PI / 2;
    });

    if (hoveredMesh) hoveredMesh.position.y = 0.15 + Math.sin(tick * 3) * 0.04;

    renderer.render(scene, camera);
  }
  loop();

  // Resize
  var resizeT;
  window.addEventListener('resize', function() {
    clearTimeout(resizeT);
    resizeT = setTimeout(function() {
      W=stage.offsetWidth||900; H=stage.offsetHeight||500;
      renderer.setSize(W,H); camera.aspect=W/H; camera.updateProjectionMatrix();
    }, 200);
  });

  // Show controls
  var mapControls = document.querySelector('.map-controls');
  if (mapControls) mapControls.innerHTML = '<button class="mc-btn" onclick="mapReset()">&#8635; Reset View</button><button class="mc-btn" id="mc-rotate" onclick="mapToggleRotate()">&#9696; Auto-Rotate</button><span class="mc-hint">Drag to rotate &middot; Scroll to zoom &middot; Click a state to expand locator</span>';
}

// 2D Canvas fallback if Three.js fails
function build2DFallback(canvas, stage) {
  var dpr = Math.min(window.devicePixelRatio||1,2);
  var W = stage.offsetWidth||900, H = stage.offsetHeight||500;
  canvas.width=W*dpr; canvas.height=H*dpr;
  canvas.style.width=W+'px'; canvas.style.height=H+'px';
  var ctx = canvas.getContext('2d');
  ctx.scale(dpr,dpr);
  var tooltip = document.getElementById('map-tooltip');
  var hovAbbr = null, paths = {}, t = {};

  function rebuild(){ t=calcMapTransform(W,H,0.04); paths=buildStatePaths(t.scale,t.ox,t.oy); }

  var COLORS={'solid-r':'#b91c1c','lean-r':'#dc2626','swing':'#d97706','lean-b':'#2563eb','solid-b':'#1d4ed8'};
  var COLORS_DARK={'solid-r':'#7f1d1d','lean-r':'#991b1b','swing':'#78350f','lean-b':'#1e3a8a','solid-b':'#1e3a8a'};

  function draw(){
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle='#0a1628';ctx.fillRect(0,0,W,H);
    var dep=Math.max(3,t.scale*5);
    Object.keys(US_PATHS).forEach(function(abbr){
      var data=MAP_STATE_DATA?MAP_STATE_DATA[abbr]:null;
      var lean=data?data.lean:'solid-b';
      var isH=abbr===hovAbbr;
      var p=paths[abbr];if(!p)return;
      var fill=isH?'#dbeafe':(COLORS[lean]||'#1d4ed8');
      var side=isH?'#93c5fd':(COLORS_DARK[lean]||'#1e3a8a');
      ctx.save();ctx.translate(dep*0.4,-dep*0.85);ctx.fillStyle=side;ctx.globalAlpha=.85;ctx.fill(p);ctx.restore();
      ctx.globalAlpha=1;ctx.fillStyle=fill;ctx.fill(p);
      ctx.strokeStyle='rgba(3,7,15,.55)';ctx.lineWidth=Math.max(.4,t.scale*.35);ctx.stroke(p);
      if(isH){ctx.strokeStyle='rgba(147,197,253,.9)';ctx.lineWidth=Math.max(1.5,t.scale*.65);ctx.stroke(p);}
    });
    ctx.textAlign='center';ctx.textBaseline='middle';
    Object.keys(US_LABELS).forEach(function(lab){
      var lp=US_LABELS[lab];
      var lx=t.ox+lp[0]*t.scale,ly=t.oy+lp[1]*t.scale;
      var tiny=['RI','DC','DE'].indexOf(lab)>=0,small=['CT','NJ','NH','VT','MA','MD','HI','WV','SC','IN'].indexOf(lab)>=0;
      var fs=Math.min(tiny?Math.max(7,t.scale*8):small?Math.max(8,t.scale*10):Math.max(9,t.scale*12),13);
      ctx.font='bold '+fs+'px "JetBrains Mono",monospace';
      ctx.fillStyle='rgba(0,0,0,.88)';ctx.fillText(lab,lx+.8,ly+.8);
      ctx.fillStyle=lab===hovAbbr?'#0f172a':'rgba(255,255,255,.92)';ctx.fillText(lab,lx,ly);
    });
  }

  function stateAt(mx,my){var k=Object.keys(US_PATHS);for(var i=k.length-1;i>=0;i--){if(paths[k[i]]&&ctx.isPointInPath(paths[k[i]],mx,my))return k[i];}return null;}
  canvas.addEventListener('mousemove',function(e){var r=canvas.getBoundingClientRect(),mx=(e.clientX-r.left)*(W/r.width),my=(e.clientY-r.top)*(H/r.height);var a=stateAt(mx,my);if(a!==hovAbbr){hovAbbr=a;draw();}canvas.style.cursor=a?'pointer':'default';});
  canvas.addEventListener('mouseleave',function(){hovAbbr=null;draw();canvas.style.cursor='default';});
  canvas.addEventListener('click',function(e){var r=canvas.getBoundingClientRect(),mx=(e.clientX-r.left)*(W/r.width),my=(e.clientY-r.top)*(H/r.height);var a=stateAt(mx,my);if(!a||!MAP_STATE_DATA)return;var d=MAP_STATE_DATA[a];if(document.getElementById('chat-state'))document.getElementById('chat-state').value=a;goPage('chat');setTimeout(function(){var ta=document.getElementById('chat-ta');if(ta){ta.value='Voting info for '+d.name;sendMsg();}},100);});
  window.addEventListener('resize',function(){W=stage.offsetWidth||900;H=stage.offsetHeight||500;canvas.width=W*dpr;canvas.height=H*dpr;canvas.style.width=W+'px';canvas.style.height=H+'px';ctx.setTransform(dpr,0,0,dpr,0,0);rebuild();draw();});
  window.mapReset=function(){hovAbbr=null;draw();};
  window.mapToggleRotate=function(){};
  rebuild();draw();
}


/* ═══════════════════════════════════════════════════════════════════
   PRODUCTION MAP FIX — Accurate D3/TopoJSON U.S. maps
   Replaces fragile canvas/WebGL state drawing with official Albers USA
   projection from us-atlas TopoJSON. Crisp SVG, accurate geometry,
   stable hover/click, responsive labels and mobile behavior.
   ═══════════════════════════════════════════════════════════════════ */
(function(){
  var FIPS_TO_ABBR={"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT","10":"DE","11":"DC","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN","19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI","27":"MN","28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ","35":"NM","36":"NY","37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA","44":"RI","45":"SC","46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA","53":"WA","54":"WV","55":"WI","56":"WY"};
  var ABBR_TO_FIPS={}; Object.keys(FIPS_TO_ABBR).forEach(function(k){ABBR_TO_FIPS[FIPS_TO_ABBR[k]]=k;});
  var D3_READY=null, US_DATA=null;
  var SMALL_OFFSETS={
    RI:[38,12], DE:[42,4], MD:[48,18], DC:[50,32], CT:[36,-10], NJ:[42,10], MA:[48,-10], NH:[34,-28], VT:[-28,-24], HI:[0,18]
  };
  var LABEL_OFFSETS={FL:[18,22], LA:[-12,18], MI:[18,8], AK:[-12,14]};
  var NE_SMALL={RI:1,DE:1,MD:1,DC:1,CT:1,NJ:1,MA:1,NH:1,VT:1};

  function loadScript(src){return new Promise(function(resolve,reject){var s=document.createElement('script');s.src=src;s.async=true;s.onload=resolve;s.onerror=reject;document.head.appendChild(s);});}
  function ensureD3(){
    if(D3_READY) return D3_READY;
    D3_READY=new Promise(function(resolve,reject){
      function loadTopo(){ if(window.topojson) resolve(); else loadScript('https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js').then(resolve).catch(reject); }
      if(window.d3) loadTopo(); else loadScript('https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js').then(loadTopo).catch(reject);
    });
    return D3_READY;
  }
  function getUS(){
    if(US_DATA) return Promise.resolve(US_DATA);
    return ensureD3().then(function(){return fetch('https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json');})
      .then(function(r){if(!r.ok) throw new Error('Could not load map topology'); return r.json();})
      .then(function(us){
        var states=topojson.feature(us, us.objects.states).features.filter(function(f){return FIPS_TO_ABBR[String(f.id).padStart(2,'0')];});
        var borders=topojson.mesh(us, us.objects.states, function(a,b){return a!==b;});
        US_DATA={states:states,borders:borders}; return US_DATA;
      });
  }
  function clearEl(el){ while(el && el.firstChild) el.removeChild(el.firstChild); }
  function statusFor(abbr){ var d=(window.MAP_STATE_DATA||{})[abbr]||{}; return d.lean||'solid-b'; }
  function stateName(abbr){ var d=(window.MAP_STATE_DATA||{})[abbr]; if(d&&d.name) return d.name; var s=(window.STATES||[]).find(function(x){return x.a===abbr;}); return s?s.n:abbr; }
  function statusLabel(l){return (typeof leanLabel==='function')?leanLabel(l):({'swing':'Battleground / Swing','lean-r':'Leans Republican','lean-b':'Leans Democrat','solid-r':'Safe Republican','solid-b':'Safe Democrat'}[l]||l);}
  function fillFor(abbr,mode){
    var l=statusFor(abbr);
    if(mode==='battleground' && !((window.BG_SET||{})[abbr])) return document.documentElement.dataset.theme==='light'?'#dbe3ee':'#142033';
    if(mode==='battleground'){
      var typ=(window.BG_TYPE||{})[abbr]||'swing';
      return {swing:'#d97706','lean-r':'#dc2626','lean-b':'#2563eb'}[typ]||'#d97706';
    }
    return {'solid-r':'#b91c1c','lean-r':'#dc2626','swing':'#d97706','lean-b':'#2563eb','solid-b':'#1d4ed8'}[l]||'#1d4ed8';
  }
  function tooltipHTML(abbr){
    var d=(window.MAP_STATE_DATA||{})[abbr]||{}; var l=d.lean||statusFor(abbr);
    return '<div class="tt-state">'+stateName(abbr)+'</div><div class="tt-abbr">'+abbr+' · Official voting information</div>'+
      '<div class="tt-row"><span class="tt-icon">📅</span><span>Registration: <span class="tt-val">'+(d.deadline||'Check official source')+'</span></span></div>'+
      '<div class="tt-row"><span class="tt-icon">🪪</span><span>ID rule: <span class="tt-val">'+(d.id||'State-specific')+'</span></span></div>'+
      '<div class="tt-row"><span class="tt-icon">🔗</span><span>Source: <span class="tt-val">Official state election office</span></span></div>'+
      '<div class="tt-lean '+(typeof leanCls==='function'?leanCls(l):'tt-swing')+'">'+statusLabel(l)+'</div>'+
      '<div class="tt-cta">Click for VoterLens guidance</div>';
  }
  function renderAccurateUSMap(opts){
    var container=opts.container, tooltip=opts.tooltip, mode=opts.mode||'explorer';
    if(!container) return;
    container.style.position='relative';
    container.style.background = mode==='explorer' ? 'rgba(3,10,28,.72)' : 'transparent';
    return getUS().then(function(data){
      clearEl(container);
      if(tooltip && tooltip.parentElement!==container) container.appendChild(tooltip);
      var W=container.clientWidth||900, H=container.clientHeight||500;
      var svg=d3.select(container).append('svg')
        .attr('class','bb-accurate-us-map')
        .attr('viewBox','0 0 '+W+' '+H)
        .attr('preserveAspectRatio','xMidYMid meet')
        .style('width','100%').style('height','100%').style('display','block');
      svg.append('rect').attr('x',0).attr('y',0).attr('width',W).attr('height',H).attr('rx',18)
        .attr('fill', mode==='explorer' ? 'rgba(3,10,28,.42)' : 'rgba(3,10,28,.20)');
      var projection=d3.geoAlbersUsa().fitExtent([[24,28],[W-24,H-34]], {type:'FeatureCollection',features:data.states});
      var path=d3.geoPath(projection);
      var g=svg.append('g').attr('class','states-layer');
      var hovered=null;
      var statePaths=g.selectAll('path.state').data(data.states).enter().append('path')
        .attr('class',function(d){return 'bb-state bb-state-'+FIPS_TO_ABBR[String(d.id).padStart(2,'0')];})
        .attr('d',path)
        .attr('fill',function(d){return fillFor(FIPS_TO_ABBR[String(d.id).padStart(2,'0')],mode);})
        .attr('fill-opacity',function(d){var ab=FIPS_TO_ABBR[String(d.id).padStart(2,'0')];return mode==='battleground'&&!((window.BG_SET||{})[ab])?0.46:0.94;})
        .attr('stroke','rgba(255,255,255,.72)')
        .attr('stroke-width',function(){return mode==='battleground'?0.9:0.8;})
        .style('cursor','pointer')
        .style('filter','drop-shadow(0px 8px 12px rgba(0,0,0,.20))')
        .on('mousemove',function(event,d){
          var ab=FIPS_TO_ABBR[String(d.id).padStart(2,'0')]; hovered=ab;
          statePaths.attr('fill-opacity',function(x){var ax=FIPS_TO_ABBR[String(x.id).padStart(2,'0')];return ax===ab?1:(mode==='battleground'&&!((window.BG_SET||{})[ax])?0.32:0.82);});
          d3.select(this).attr('stroke','#ffffff').attr('stroke-width',2.2).raise();
          if(tooltip){
            tooltip.innerHTML=tooltipHTML(ab); tooltip.classList.add('show');
            var rect=container.getBoundingClientRect();
            var tw=tooltip.offsetWidth||260, th=tooltip.offsetHeight||140;
            var x=event.clientX-rect.left+16, y=event.clientY-rect.top+16;
            if(x+tw>rect.width-10) x=event.clientX-rect.left-tw-16;
            if(y+th>rect.height-10) y=event.clientY-rect.top-th-16;
            tooltip.style.left=Math.max(10,x)+'px'; tooltip.style.top=Math.max(10,y)+'px'; tooltip.style.bottom='auto'; tooltip.style.transform='none';
          }
        })
        .on('mouseleave',function(){ hovered=null; statePaths.attr('fill-opacity',function(x){var ax=FIPS_TO_ABBR[String(x.id).padStart(2,'0')];return mode==='battleground'&&!((window.BG_SET||{})[ax])?0.46:0.94;}).attr('stroke','rgba(255,255,255,.72)').attr('stroke-width',mode==='battleground'?0.9:0.8); if(tooltip) tooltip.classList.remove('show');})
        .on('click',function(event,d){
          var ab=FIPS_TO_ABBR[String(d.id).padStart(2,'0')];
          if(document.getElementById('chat-state')) document.getElementById('chat-state').value=ab;
          if(typeof goPage==='function') goPage('chat');
          setTimeout(function(){var ta=document.getElementById('chat-ta');if(ta){ta.value='Give me official voting information for '+stateName(ab)+'.'; if(typeof sendMsg==='function') sendMsg();}},120);
        });
      g.append('path').datum(data.borders).attr('d',path).attr('fill','none').attr('stroke','rgba(3,7,15,.75)').attr('stroke-width',0.75).attr('pointer-events','none');
      // Labels layer
      var labels=svg.append('g').attr('class','labels-layer').attr('pointer-events','none');
      data.states.forEach(function(f){
        var ab=FIPS_TO_ABBR[String(f.id).padStart(2,'0')]; var c=path.centroid(f); if(!c||isNaN(c[0])||isNaN(c[1])) return;
        var off=SMALL_OFFSETS[ab]||LABEL_OFFSETS[ab]||[0,0]; var lx=c[0]+off[0], ly=c[1]+off[1];
        var bg=((window.BG_SET||{})[ab]);
        if(mode==='battleground' && !bg && W<700) return;
        if(SMALL_OFFSETS[ab]) labels.append('line').attr('x1',c[0]).attr('y1',c[1]).attr('x2',lx-4).attr('y2',ly).attr('stroke','rgba(255,255,255,.45)').attr('stroke-width',0.7);
        labels.append('text').attr('x',lx).attr('y',ly).attr('text-anchor','middle').attr('dominant-baseline','middle')
          .attr('font-family','JetBrains Mono, monospace').attr('font-weight',700)
          .attr('font-size', mode==='battleground'?(bg?12:8):(NE_SMALL[ab]?10:12))
          .attr('paint-order','stroke').attr('stroke','rgba(3,7,15,.9)').attr('stroke-width',3).attr('fill','#f8fafc')
          .style('letter-spacing','.02em').text(ab);
      });
      if(mode==='battleground'){
        var pulses=svg.append('g').attr('pointer-events','none');
        data.states.forEach(function(f){var ab=FIPS_TO_ABBR[String(f.id).padStart(2,'0')]; if(!((window.BG_SET||{})[ab]))return; var c=path.centroid(f); if(!c||isNaN(c[0]))return; pulses.append('circle').attr('cx',c[0]).attr('cy',c[1]).attr('r',9).attr('fill','none').attr('stroke',fillFor(ab,'battleground')).attr('stroke-width',1.5).attr('opacity',0.55).append('animate').attr('attributeName','r').attr('values','5;14;5').attr('dur','2.8s').attr('repeatCount','indefinite');});
      }
      var title= mode==='explorer' ? 'Official 50-State Voting Information Map' : 'Battleground State Information Map';
      svg.append('text').attr('x',22).attr('y',28).attr('font-family','JetBrains Mono, monospace').attr('font-size',11).attr('letter-spacing','.08em').attr('fill','rgba(248,250,252,.70)').text(title.toUpperCase());
      if(opts.onReady) opts.onReady();
    }).catch(function(err){
      console.warn('Accurate map failed; using stable fallback',err);
      container.innerHTML='<div style="height:100%;display:grid;place-items:center;text-align:center;padding:28px;color:var(--text2);font-family:var(--sans)"><div><div style="font-family:var(--serif);font-size:24px;color:var(--text);margin-bottom:8px">Map could not load</div><div style="font-size:13px;line-height:1.6">Please check your internet connection. VoterLens still works through the state selector and AI guidance.</div></div></div>';
    });
  }

  window.initBattlegroundMap=function(){
    var canvas=document.getElementById('bg-map-canvas'); if(!canvas) return; if(canvas._accurateBuilt) return; canvas._accurateBuilt=true;
    var wrap=canvas.parentElement; canvas.remove();
    var tip=document.createElement('div'); tip.className='globe-tooltip'; tip.id='bg-map-tooltip'; wrap.appendChild(tip);
    function draw(){ renderAccurateUSMap({container:wrap,tooltip:tip,mode:'battleground'}); }
    draw(); var timer; window.addEventListener('resize',function(){clearTimeout(timer);timer=setTimeout(draw,220);});
  };

  window.initExplorerMap=function(){
    var canvas=document.getElementById('map-canvas'); if(!canvas) return; if(canvas._accurateBuilt) return; canvas._accurateBuilt=true;
    var stage=canvas.parentElement; var tooltip=document.getElementById('map-tooltip'); canvas.remove();
    function draw(){ renderAccurateUSMap({container:stage,tooltip:tooltip,mode:'explorer'}); }
    draw(); var timer; window.addEventListener('resize',function(){clearTimeout(timer);timer=setTimeout(draw,220);});
    var controls=document.querySelector('.map-controls'); if(controls) controls.innerHTML='<span class="mc-hint">Accurate Albers USA projection · Hover for official state details · Click for VoterLens guidance</span>';
    window.mapReset=function(){draw();}; window.mapToggleRotate=function(){};
  };
})();


// ═══════════════════════════════════════════════════════════════════
// BOOT — fires after window.load so all CSS dimensions are settled
// ═══════════════════════════════════════════════════════════════════
function bootGraphics() {
  initHeroGlobe();
  initBattlegroundMap();
  initExplorerMap();
}

if (document.readyState === 'complete') {
  setTimeout(bootGraphics, 30);
} else {
  window.addEventListener('load', function () { setTimeout(bootGraphics, 30); });
}

// generatePlan function (was missing)
function generatePlan() {
  var stAbbr = document.getElementById('plan-state') ? document.getElementById('plan-state').value : 'GA';
  var stName = (STATES || []).find(function(s){ return s.a === stAbbr; }) || {n:'Georgia',a:'GA'};
  var reg    = document.querySelector('.ps-opt[data-group="reg"].sel');
  var method = document.querySelector('.ps-opt[data-group="method"].sel');
  var first  = document.querySelector('.ps-opt[data-group="first"].sel');
  var regVal = reg    ? reg.getAttribute('data-val')    : 'unsure';
  var mVal   = method ? method.getAttribute('data-val') : 'inperson';
  var fVal   = first  ? first.getAttribute('data-val')  : 'no';

  var html = '<div class="pr-section">';
  html += '<div class="pr-section-title">Registration Checklist</div><ul class="pr-checklist">';
  if (regVal !== 'yes') {
    html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Register to vote at <a href="https://vote.gov/register/' + stAbbr.toLowerCase() + '/" target="_blank">Vote.gov/register/' + stAbbr.toLowerCase() + '</a></span></li>';
    html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Check ' + stName.n + '\'s registration deadline at your Secretary of State website.</span></li>';
  }
  html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Verify your registration at <a href="https://vote.gov/" target="_blank">Vote.gov</a> or your state\'s My Voter page.</span></li>';
  html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Confirm your address is current on your registration.</span></li>';
  html += '</ul></div>';

  html += '<div class="pr-section"><div class="pr-section-title">ID Checklist</div><ul class="pr-checklist">';
  html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Check ' + stName.n + '\'s ID requirements at your Secretary of State website.</span></li>';
  if (fVal === 'yes') html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>First-time voters: bring photo ID and a proof-of-address document.</span></li>';
  html += '</ul></div>';

  html += '<div class="pr-section"><div class="pr-section-title">' + (mVal==='mail'?'Mail-In Plan':mVal==='early'?'Early Voting Plan':'Election Day Plan') + '</div><ul class="pr-checklist">';
  if (mVal === 'mail') {
    html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Request your absentee/mail-in ballot early — check ' + stName.n + '\'s deadline.</span></li>';
    html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Follow all ballot instructions exactly. Return it well before the deadline.</span></li>';
  } else if (mVal === 'early') {
    html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Look up early voting dates and locations at the ' + stName.n + ' Secretary of State website.</span></li>';
    html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Bring your ID. Early voting locations may differ from your Election Day polling place.</span></li>';
  } else {
    html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>Find your polling place at <a href="https://vote.gov/" target="_blank">Vote.gov</a> before Election Day.</span></li>';
    html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>If you are in line before polls close, you have the right to vote.</span></li>';
  }
  html += '</ul></div>';

  html += '<div class="pr-section"><div class="pr-section-title">Your Rights</div><ul class="pr-checklist">';
  html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>If turned away, request a <strong>provisional ballot</strong>. You have the legal right to one.</span></li>';
  html += '<li class="pr-item"><div class="pr-check" onclick="this.classList.toggle(\'done\')">&#10003;</div><span>If you experience intimidation, call <strong>866-OUR-VOTE</strong> (866-687-8683) immediately.</span></li>';
  html += '</ul></div>';

  html += '<div class="pr-section"><div class="pr-section-title">Official Sources</div><ul class="pr-checklist" style="gap:6px">';
  html += '<li class="pr-item">&#127760; <a href="https://vote.gov/register/' + stAbbr.toLowerCase() + '/" target="_blank">Vote.gov — ' + stName.n + '</a></li>';
  html += '<li class="pr-item">&#127760; <a href="https://www.eac.gov/voters/register-and-vote-in-your-state" target="_blank">EAC — State Voter Guide</a></li>';
  html += '<li class="pr-item">&#127760; <a href="https://www.usa.gov/state-election-office" target="_blank">USA.gov — State Election Offices</a></li>';
  html += '<li class="pr-item">&#128222; <a href="tel:18668678683">866-OUR-VOTE — Election Protection</a></li>';
  html += '</ul></div>';

  document.getElementById('plan-result-content').innerHTML = html;
  var res = document.getElementById('plan-result');
  res.classList.add('show');
  res.scrollIntoView({behavior:'smooth', block:'start'});
  if (typeof earnBadge === 'function') earnBadge('plan');
}



// Hook sendMsg to track chat count + badge
var _origSendMsg=sendMsg;
sendMsg=function(){
  chatCount++;
  try{localStorage.setItem('vl_chat_count',chatCount);}catch(e){}
  if(chatCount>=1)earnBadge('firstask');
  if(chatCount>=5)earnBadge('chat5');
  _origSendMsg.apply(this,arguments);
};

// Hook cardClick to track map state clicks  
var _origCardClick=cardClick;
cardClick=function(q){
  mapClickCount++;
  try{localStorage.setItem('vl_map_clicks',mapClickCount);}catch(e){}
  earnBadge('state');
  if(mapClickCount>=3)earnBadge('map');
  _origCardClick.apply(this,arguments);
};

// Earn timeline badge when visiting
document.addEventListener('DOMContentLoaded',function(){
  // Track source clicks
  document.addEventListener('click',function(e){
    var a=e.target.closest('a[href*="gov"],[href*="vote.gov"]');
    if(a)earnBadge('sources');
  });
  // Earn emer badge when opened
  var ef=document.getElementById('emer-modal');
  if(ef){
    var obs2=new MutationObserver(function(){if(ef.classList.contains('open'))earnBadge('emer');});
    obs2.observe(ef,{attributes:true,attributeFilter:['class']});
  }
  updateBadgeUI();
});

// Override goPage to earn timeline badge
// timeline badge handled inside new-pages goPage

// ── SCROLL REVEAL (extend existing) ─────────────────────────────────
var _origReveal=revealOnScroll;
revealOnScroll=function(){
  if(_origReveal)_origReveal();
  // Timeline items
  document.querySelectorAll('.tl-item,.badge-card').forEach(function(el){
    var r=el.getBoundingClientRect();
    if(r.top<window.innerHeight-60)el.classList.add('visible');
  });
};
window.addEventListener('scroll',revealOnScroll,{passive:true});

// ── ENHANCED SYSTEM PROMPT ────────────────────────────────────────────
// Override sendMsg to use richer system prompt that covers all scenarios
// sendMsg enhancement handled by wrapper above


// ── CIVIC BADGES (restored) ──────────────────────────────────────────
var BADGE_DEFS = [
  {id:'firstask',icon:'&#128172;',name:'First Question Asked',desc:'You asked VoterLens your first voting question.',action:'Ask a question in the chat'},
  {id:'plan',icon:'&#128203;',name:'Voting Plan Built',desc:'You created a personalized voting plan.',action:'Build your voting plan'},
  {id:'state',icon:'&#128506;',name:'State Explorer',desc:'You explored voting info for a state.',action:'Click a state on the map'},
  {id:'timeline',icon:'&#128220;',name:'History Seeker',desc:'You explored the Democracy Timeline.',action:'Visit the History page'},
  {id:'emer',icon:'&#128680;',name:'Rights Defender',desc:'You learned about emergency voting rights.',action:'Open the Emergency Help menu'},
  {id:'sources',icon:'&#128737;',name:'Source Checker',desc:'You clicked an official government source link.',action:'Click any source link in an answer'},
  {id:'chat5',icon:'&#128441;',name:'Civic Learner',desc:'You asked 5 voting questions.',action:'Ask 5 questions in the chat'},
  {id:'map',icon:'&#127775;',name:'Democracy Researcher',desc:'You explored 3 different states.',action:'Explore 3 states on the map'},
];
var earnedBadges = [];
try{ earnedBadges=JSON.parse(localStorage.getItem('vl_badges')||'[]'); }catch(e){}
var chatCount=0;
try{ chatCount=parseInt(localStorage.getItem('vl_chat_count')||'0'); }catch(e){}
var mapClickCount=0;
try{ mapClickCount=parseInt(localStorage.getItem('vl_map_clicks')||'0'); }catch(e){}

function earnBadge(id){
  if(earnedBadges.indexOf(id)>=0)return;
  earnedBadges.push(id);
  try{localStorage.setItem('vl_badges',JSON.stringify(earnedBadges));}catch(e){}
  updateBadgeUI();
  showBadgeToast(id);
}
function showBadgeToast(id){
  var def=BADGE_DEFS.find(function(b){return b.id===id;});if(!def)return;
  var t=document.createElement('div');
  t.style.cssText='position:fixed;bottom:90px;left:50%;transform:translateX(-50%);z-index:700;background:rgba(5,12,30,.95);border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:10px 18px;display:flex;align-items:center;gap:12px;font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--gold2);backdrop-filter:blur(20px);box-shadow:0 8px 32px rgba(0,0,0,.5);opacity:0;transition:opacity .3s;';
  t.innerHTML='<span style="font-size:20px">'+def.icon+'</span><div><div style="font-weight:700">Badge Earned</div><div style="opacity:.7;margin-top:2px">'+def.name+'</div></div>';
  document.body.appendChild(t);
  requestAnimationFrame(function(){t.style.opacity='1';});
  setTimeout(function(){t.style.opacity='0';setTimeout(function(){t.remove();},400);},3000);
}
function initBadges(){
  var grid=document.getElementById('badges-grid');if(!grid)return;
  grid.innerHTML=BADGE_DEFS.map(function(b,i){
    var earned=earnedBadges.indexOf(b.id)>=0;
    return '<div class="badge-card'+(earned?' earned':'')+'" style="transition-delay:'+(i*.07)+'s">'+
      '<span class="badge-icon">'+b.icon+'</span>'+
      '<div class="badge-name">'+b.name+'</div>'+
      '<div class="badge-desc">'+b.desc+'</div>'+
      '<div class="badge-status">'+(earned?'<div class="badge-earned-lbl">&#10003; Earned</div>':'<div class="badge-locked-lbl">&#128274; Locked</div><button class="badge-unlock-btn" onclick="goPage(\'chat\')">'+b.action+' &#8594;</button>')+'</div></div>';
  }).join('');
  updateBadgeUI();
  setTimeout(revealOnScroll,100);
}
function updateBadgeUI(){
  var bar=document.getElementById('bp-bar'),lbl=document.getElementById('bp-label');
  var pct=Math.round(earnedBadges.length/BADGE_DEFS.length*100);
  if(bar)bar.style.width=Math.max(pct,4)+'%';
  if(lbl)lbl.textContent=earnedBadges.length+' of '+BADGE_DEFS.length+' milestones reached';
}
</script>

<!-- ═══ VOTING PLAN PAGE ═══ -->
<div id="pg-plan" class="page">
  <div class="plan-hero">
    <div class="section-tag">Personalized</div>
    <div class="plan-title">Build Your Voting Plan</div>
    <p class="plan-sub">Provide your state and preferences. VoterLens generates a structured voting plan with registration steps, ID requirements, and official source links.</p>
  </div>
  <div class="plan-steps" id="plan-steps">
    <div class="plan-step">
      <div class="ps-label"><div class="ps-num">1</div>Your State</div>
      <div class="ps-title">Which state are you voting in?</div>
      <select class="state-sel" id="plan-state" style="width:100%;height:40px;border-radius:8px;border:1px solid var(--border);background:var(--surface);color:var(--text);font-family:var(--sans);font-size:14px;padding:0 12px;outline:none;cursor:pointer;"></select>
    </div>
    <div class="plan-step">
      <div class="ps-label"><div class="ps-num">2</div>Registration Status</div>
      <div class="ps-title">Are you currently registered to vote?</div>
      <div class="ps-options">
        <button class="ps-opt" data-group="reg" data-val="yes" onclick="selOpt(this)">✅ Yes, I'm registered</button>
        <button class="ps-opt" data-group="reg" data-val="no" onclick="selOpt(this)">❌ Not yet registered</button>
        <button class="ps-opt" data-group="reg" data-val="unsure" onclick="selOpt(this)">🤔 Not sure</button>
      </div>
    </div>
    <div class="plan-step">
      <div class="ps-label"><div class="ps-num">3</div>How You Plan to Vote</div>
      <div class="ps-title">Which voting method do you prefer?</div>
      <div class="ps-options">
        <button class="ps-opt" data-group="method" data-val="inperson" onclick="selOpt(this)">🏛️ In-person on Election Day</button>
        <button class="ps-opt" data-group="method" data-val="early" onclick="selOpt(this)">📅 Early in-person voting</button>
        <button class="ps-opt" data-group="method" data-val="mail" onclick="selOpt(this)">✉️ Mail-in / Absentee ballot</button>
        <button class="ps-opt" data-group="method" data-val="unsure" onclick="selOpt(this)">🤔 Haven't decided yet</button>
      </div>
    </div>
    <div class="plan-step">
      <div class="ps-label"><div class="ps-num">4</div>Voter Experience</div>
      <div class="ps-title">Is this your first time voting?</div>
      <div class="ps-options">
        <button class="ps-opt" data-group="first" data-val="yes" onclick="selOpt(this)">🌟 Yes, first time!</button>
        <button class="ps-opt" data-group="first" data-val="no" onclick="selOpt(this)">🗳️ No, I've voted before</button>
      </div>
    </div>
    <div class="plan-step">
      <div class="ps-label"><div class="ps-num">5</div>Special Needs</div>
      <div class="ps-title">Do you need any accommodations? (select all that apply)</div>
      <div class="ps-options">
        <button class="ps-opt" data-group="needs" data-val="transport" data-multi="true" onclick="selOptMulti(this)">🚗 Transportation help</button>
        <button class="ps-opt" data-group="needs" data-val="accessibility" data-multi="true" onclick="selOptMulti(this)">♿ Accessibility needs</button>
        <button class="ps-opt" data-group="needs" data-val="language" data-multi="true" onclick="selOptMulti(this)">🌐 Language assistance</button>
        <button class="ps-opt" data-group="needs" data-val="none" data-multi="true" onclick="selOptMulti(this)">✅ No special needs</button>
      </div>
    </div>
    <button class="plan-generate-btn" onclick="generatePlan()">Generate My Voting Plan ✨</button>
  </div>
  <div class="plan-result" id="plan-result">
    <div class="pr-head">📋 Your Personal Voting Plan</div>
    <div id="plan-result-content"></div>
    <div class="pr-actions">
      <button class="pr-btn primary" onclick="askPlanQuestion()">Ask VoterLens a Question</button>
      <button class="pr-btn" onclick="window.print()">🖨️ Print Plan</button>
      <button class="pr-btn" onclick="copyPlan()">📋 Copy Plan</button>
    </div>
  </div>
</div>

<!-- ═══ DEMOCRACY TIMELINE PAGE ═══ -->
<div id="pg-timeline" class="page">
  <div class="tl-hero">
    <div class="section-tag" style="justify-content:center">The Story of American Democracy</div>
    <div class="tl-title">The Long Fight<br/>for the Vote</div>
    <p class="tl-sub">Scroll through the moments that defined who gets to participate in American democracy — and why your vote matters today.</p>
    <div class="tl-scroll-hint" style="font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--text3);margin-top:4px">Scroll to read</div>
  </div>
  <div class="tl-track" id="tl-track">

    <div class="tl-item">
      <div class="tl-dot" style="background:rgba(185,28,28,.15);border-color:rgba(185,28,28,.4)">📜</div>
      <div class="tl-card">
        <div class="tl-year">1776</div>
        <div class="tl-event">The Founding — But Not For Everyone</div>
        <div class="tl-desc">The Declaration of Independence promised liberty, but voting was limited to white male property owners — roughly 6% of the population. The ideals of democracy and its reality were far apart from the start.</div>
      </div>
    </div>

    <div class="tl-item">
      <div class="tl-dot" style="background:rgba(29,78,196,.15);border-color:rgba(29,78,196,.4)">⚖️</div>
      <div class="tl-card">
        <div class="tl-year">1870</div>
        <div class="tl-event">15th Amendment: Race No Longer a Bar</div>
        <div class="tl-desc">The 15th Amendment gave Black men the right to vote — but states immediately fought back with poll taxes, literacy tests, and grandfather clauses designed to suppress Black voters.</div>
        <div class="tl-quote">"The right of citizens of the United States to vote shall not be denied or abridged...on account of race, color, or previous condition of servitude."</div>
      </div>
    </div>

    <div class="tl-item">
      <div class="tl-dot" style="background:rgba(245,158,11,.15);border-color:rgba(245,158,11,.4)">🌟</div>
      <div class="tl-card">
        <div class="tl-year">1920</div>
        <div class="tl-event">19th Amendment: Women Win the Vote</div>
        <div class="tl-desc">After 72 years of organizing, protests, arrests, and hunger strikes, the 19th Amendment was ratified. Women — over half the population — finally had the constitutional right to vote.</div>
        <div class="tl-quote">"There will never be a new world order until women are a part of it." — Alice Paul</div>
      </div>
    </div>

    <div class="tl-item">
      <div class="tl-dot" style="background:rgba(185,28,28,.15);border-color:rgba(185,28,28,.4)">✊</div>
      <div class="tl-card">
        <div class="tl-year">1965</div>
        <div class="tl-event">Voting Rights Act of 1965</div>
        <div class="tl-desc">After Bloody Sunday on the Edmund Pettus Bridge in Selma, Alabama, Congress passed landmark legislation outlawing discriminatory voting practices — the most powerful voting rights law in American history.</div>
        <div class="tl-quote">"The vote is the most powerful nonviolent change agent you have in a democratic society." — John Lewis</div>
      </div>
    </div>

    <div class="tl-item">
      <div class="tl-dot" style="background:rgba(29,78,196,.15);border-color:rgba(29,78,196,.4)">🎓</div>
      <div class="tl-card">
        <div class="tl-year">1971</div>
        <div class="tl-event">26th Amendment: Votes at 18</div>
        <div class="tl-desc">Young Americans serving in Vietnam couldn't vote in the elections that sent them to war. The 26th Amendment lowered the voting age from 21 to 18 — the fastest-ratified amendment in U.S. history.</div>
        <div class="tl-quote">"Old enough to fight, old enough to vote."</div>
      </div>
    </div>

    <div class="tl-item">
      <div class="tl-dot" style="background:rgba(245,158,11,.15);border-color:rgba(245,158,11,.4)">♿</div>
      <div class="tl-card">
        <div class="tl-year">1984</div>
        <div class="tl-event">Voting Accessibility for the Elderly and Handicapped Act</div>
        <div class="tl-desc">Federal law required polling places to be physically accessible to elderly and disabled voters — a recognition that the right to vote must include the ability to actually cast that vote.</div>
      </div>
    </div>

    <div class="tl-item">
      <div class="tl-dot" style="background:rgba(96,165,250,.15);border-color:rgba(96,165,250,.4)">🗺️</div>
      <div class="tl-card">
        <div class="tl-year">1993</div>
        <div class="tl-event">Motor Voter Act (NVRA)</div>
        <div class="tl-desc">The National Voter Registration Act made it possible to register to vote at the DMV, public assistance offices, and by mail — removing major barriers that had kept millions off the rolls.</div>
      </div>
    </div>

    <div class="tl-item">
      <div class="tl-dot" style="background:rgba(185,28,28,.15);border-color:rgba(185,28,28,.4)">📱</div>
      <div class="tl-card">
        <div class="tl-year">2000s–Now</div>
        <div class="tl-event">Voter ID Laws and the New Battleground</div>
        <div class="tl-desc">Strict photo ID laws have swept many states, with supporters citing security and critics citing suppression. Courts continue to debate their constitutionality. The fight over who can vote — and how — continues.</div>
      </div>
    </div>

    <div class="tl-item">
      <div class="tl-dot" style="background:rgba(245,158,11,.15);border-color:rgba(245,158,11,.4)">🤖</div>
      <div class="tl-card">
        <div class="tl-year">Today</div>
        <div class="tl-event">AI, Misinformation, and the Future of Democracy</div>
        <div class="tl-desc">Artificial intelligence is being used both to spread election misinformation and to combat it. Deepfakes, synthetic media, and algorithmic amplification are reshaping how voters access information. Tools like VoterLens are part of the civic response.</div>
      </div>
    </div>

    <div class="tl-ending">
      <div class="tl-ending-title">The next chapter belongs to you.</div>
      <p class="tl-ending-sub">Every person on this timeline fought so you could cast a ballot. Your vote is the continuation of that story — and VoterLens is here to help you exercise it.</p>
      <button class="mc-btn" style="margin:0 auto;display:block;height:36px;padding:0 24px" onclick="goPage('chat')">Ask VoterLens About Your Rights →</button>
    </div>
  </div>
</div>

<!-- ═══ CIVIC BADGES PAGE ═══ -->
<div id="pg-badges" class="page">
  <div class="badges-hero">
    <div class="section-tag" style="justify-content:center">Civic Knowledge Tracker</div>
    <div class="badges-title">Civic Knowledge Milestones</div>
    <p class="badges-sub">Track your civic knowledge milestones. Each reflects real understanding of voting rights, registration processes, and civic protections.</p>
  </div>
  <div class="badges-progress" id="badges-progress">
    <div class="bp-bar-wrap"><div class="bp-bar" id="bp-bar" style="width:12%"></div></div>
    <div class="bp-label" id="bp-label">1 of 8 milestones reached</div>
  </div>
  <div class="badges-grid" id="badges-grid"></div>
</div>



<script>
// ═══ VoterLens 3D Polish Layer — additive only, no chatbot/source logic changed ═══
(function(){
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function ready(fn){ if(document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  ready(function(){
    // Ambient depth elements
    if(!document.querySelector('.bb-3d-ambient')){
      const amb=document.createElement('div');
      amb.className='bb-3d-ambient';
      amb.innerHTML='<div class="bb-3d-orb o1"></div><div class="bb-3d-orb o2"></div><div class="bb-3d-wire"></div>';
      document.body.prepend(amb);
    }
    // Hero status chips for polished 3D command-center feel
    const heroInner=document.querySelector('.hero-inner');
    if(heroInner && !heroInner.querySelector('.bb-hero-console')){
      const consoleEl=document.createElement('div');
      consoleEl.className='bb-hero-console';
      consoleEl.innerHTML='<span class="bb-console-chip"><span class="bb-console-dot"></span>Official Sources</span><span class="bb-console-chip"><span class="bb-console-dot"></span>50-State Coverage</span><span class="bb-console-chip"><span class="bb-console-dot"></span>Rights Guidance</span>';
      const stats=heroInner.querySelector('.hero-stats');
      heroInner.insertBefore(consoleEl, stats || null);
    }
    // Map depth label
    document.querySelectorAll('.map-stage').forEach(stage=>{
      if(!stage.querySelector('.bb-map-depth-label')){
        const label=document.createElement('div');
        label.className='bb-map-depth-label';
        label.textContent='Civic Map Layer';
        stage.appendChild(label);
      }
    });
    // Subtle 3D tilt — visual only, low impact
    const tiltEls=[...document.querySelectorAll('.p-box,.info-card,.q-card,.about-card,.plan-step,.tl-card,.badge-card,.state-card,.map-stage')];
    tiltEls.forEach(el=>el.classList.add('bb-tilt-ready'));
    if(!reduce){
      const maxTilt = 5;
      tiltEls.forEach(el=>{
        el.addEventListener('pointermove', e=>{
          if(window.innerWidth < 760) return;
          const r=el.getBoundingClientRect();
          const x=(e.clientX-r.left)/r.width-.5;
          const y=(e.clientY-r.top)/r.height-.5;
          el.style.transform=`perspective(1000px) rotateX(${(-y*maxTilt).toFixed(2)}deg) rotateY(${(x*maxTilt).toFixed(2)}deg) translateZ(0)`;
        }, {passive:true});
        el.addEventListener('pointerleave', ()=>{ el.style.transform=''; }, {passive:true});
      });
      // gentle hero parallax on desktop
      const hero=document.querySelector('.hero');
      if(hero){
        hero.addEventListener('pointermove', e=>{
          if(window.innerWidth < 900) return;
          const r=hero.getBoundingClientRect();
          const x=(e.clientX-r.left)/r.width-.5;
          const y=(e.clientY-r.top)/r.height-.5;
          document.documentElement.style.setProperty('--bb-par-x', (x*10).toFixed(2)+'px');
          document.documentElement.style.setProperty('--bb-par-y', (y*10).toFixed(2)+'px');
          const globe=document.querySelector('.globe-wrap');
          if(globe) globe.style.translate=`${(x*-12).toFixed(1)}px ${(y*-10).toFixed(1)}px`;
        }, {passive:true});
        hero.addEventListener('pointerleave', ()=>{ const globe=document.querySelector('.globe-wrap'); if(globe) globe.style.translate=''; }, {passive:true});
      }
    }
  });
})();
</script>


<style id="vl-final-polish">
/* Final VoterLens polish + official locator experience */
.hero-h1{display:flex;flex-direction:column;gap:10px;align-items:flex-start;perspective:900px}
.hero-h1 span{display:inline-flex;align-items:center;line-height:.88;padding:.02em .12em .08em;border-radius:18px;background:linear-gradient(135deg,rgba(255,255,255,.035),rgba(255,255,255,0));border:1px solid rgba(255,255,255,.045);transform-style:preserve-3d;letter-spacing:-.04em}
[data-theme="light"] .hero-h1 span{background:linear-gradient(135deg,rgba(255,255,255,.86),rgba(255,255,255,.25));border-color:rgba(13,21,38,.08);box-shadow:0 18px 50px rgba(29,78,216,.10)}
.h1-l1::after,.h1-l2::after,.h1-l3::after{content:"";width:clamp(34px,5vw,74px);height:3px;margin-left:14px;border-radius:99px;background:currentColor;opacity:.32;box-shadow:0 0 18px currentColor}
.h1-l3{color:transparent!important;-webkit-text-stroke:1.5px rgba(245,240,232,.38)!important}
[data-theme="light"] .h1-l3{-webkit-text-stroke:1.5px rgba(13,21,38,.42)!important}
.globe-wrap{pointer-events:auto!important;cursor:grab;overflow:visible!important;filter:drop-shadow(0 30px 70px rgba(29,78,216,.24)) saturate(1.05)}
.globe-wrap:active{cursor:grabbing}.globe-wrap::before{content:"Drag the globe";position:absolute;left:50%;bottom:8%;transform:translateX(-50%);font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--text3);padding:6px 10px;border:1px solid var(--border);border-radius:99px;background:rgba(5,12,30,.55);backdrop-filter:blur(10px);opacity:0;transition:opacity .2s;z-index:3}.globe-wrap:hover::before{opacity:1}[data-theme="light"] .globe-wrap{filter:drop-shadow(0 28px 58px rgba(13,21,38,.16)) saturate(.95) brightness(1.03)}[data-theme="light"] .globe-wrap::before{background:rgba(255,255,255,.76)}
.map-stage{background:radial-gradient(circle at 50% 35%,rgba(96,165,250,.18),transparent 42%),linear-gradient(145deg,rgba(6,14,32,.96),rgba(7,15,34,.72))!important;transform-style:preserve-3d;box-shadow:0 42px 120px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.045),inset 0 1px 0 rgba(255,255,255,.08)!important}.map-stage::before{content:"";position:absolute;inset:12px;border-radius:16px;border:1px solid rgba(255,255,255,.08);pointer-events:none;z-index:1}.map-stage:hover{transform:perspective(1100px) rotateX(2.5deg) translateY(-3px)}[data-theme="light"] .map-stage{background:radial-gradient(circle at 50% 28%,rgba(29,78,216,.16),transparent 45%),linear-gradient(145deg,#f8fbff,#dce8ff)!important;box-shadow:0 36px 90px rgba(29,78,216,.18),0 0 0 1px rgba(13,21,38,.08),inset 0 1px 0 rgba(255,255,255,.95)!important}.bb-state{transition:transform .18s ease, filter .18s ease, fill-opacity .18s ease}.bb-state:hover{filter:drop-shadow(0 12px 22px rgba(255,255,255,.34)) brightness(1.08)}
#pg-chat .chat-main::before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 20% 10%,rgba(220,38,38,.10),transparent 28%),radial-gradient(circle at 80% 18%,rgba(29,78,216,.12),transparent 30%),linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:auto,auto,46px 46px,46px 46px;pointer-events:none}.cw-pill,.side-link,.p-hint{position:relative;overflow:hidden}.cw-pill::after,.side-link::after,.p-hint::after{content:"";position:absolute;inset:0;background:linear-gradient(120deg,transparent,rgba(255,255,255,.12),transparent);transform:translateX(-120%);transition:transform .55s}.cw-pill:hover::after,.side-link:hover::after,.p-hint:hover::after{transform:translateX(120%)}
.badges-progress{max-width:760px;margin:-22px auto 26px;padding:18px;border:1px solid var(--border);border-radius:18px;background:var(--surface);backdrop-filter:blur(16px);box-shadow:0 18px 50px rgba(0,0,0,.18)}.bp-bar-wrap{height:11px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden;border:1px solid var(--border)}.bp-bar{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--red2),var(--gold2),var(--blue3));box-shadow:0 0 18px var(--gold-glow);transition:width .6s cubic-bezier(.22,1,.36,1)}.bp-label{text-align:center;margin-top:10px;font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--text2)}.badge-card{min-height:214px;display:flex;flex-direction:column;justify-content:center}.badge-card.earned .badge-icon{filter:drop-shadow(0 0 14px var(--gold-glow));animation:badgeFloat 3.8s ease-in-out infinite}@keyframes badgeFloat{50%{transform:translateY(-5px) rotate(-2deg)}}
.state-locator-panel{max-width:1100px;margin:22px auto 0;border:1px solid var(--border);border-radius:22px;background:linear-gradient(145deg,rgba(255,255,255,.07),rgba(255,255,255,.025));backdrop-filter:blur(18px);box-shadow:0 24px 70px rgba(0,0,0,.22);padding:20px;overflow:hidden}.locator-empty{text-align:center;padding:22px;color:var(--text2)}.locator-empty h3{font-family:var(--serif);font-size:26px;color:var(--text);margin:4px 0 8px}.locator-kicker,.locator-trust{font-family:var(--mono);font-size:10px;letter-spacing:.13em;text-transform:uppercase;color:var(--gold2)}.locator-grid{display:grid;grid-template-columns:1.05fr 1.6fr;gap:18px;align-items:stretch}.locator-state-card{border:1px solid var(--border);border-radius:18px;background:rgba(5,12,30,.48);padding:22px;position:relative;overflow:hidden}.locator-state-card::after{content:"";position:absolute;right:-50px;top:-50px;width:160px;height:160px;border-radius:50%;background:radial-gradient(circle,rgba(245,158,11,.22),transparent 66%)}.locator-name{font-family:var(--serif);font-size:clamp(28px,4vw,46px);line-height:1;color:var(--text);margin:10px 0}.locator-sub{font-size:13px;color:var(--text2);line-height:1.6}.locator-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.locator-btn{display:flex;align-items:flex-start;gap:11px;padding:14px;border-radius:14px;border:1px solid var(--border);background:var(--surface);color:var(--text);transition:all .2s;min-height:88px}.locator-btn:hover{transform:translateY(-3px);border-color:rgba(245,158,11,.35);background:rgba(245,158,11,.07);box-shadow:0 16px 38px rgba(0,0,0,.20)}.locator-btn span{font-size:20px;line-height:1}.locator-btn strong{display:block;font-size:13px;margin-bottom:4px}.locator-btn small{display:block;color:var(--text3);font-size:11px;line-height:1.45}.locator-search{margin-top:14px;display:flex;gap:9px}.locator-search input{flex:1;height:40px;border-radius:12px;border:1px solid var(--border);background:var(--surface);color:var(--text);padding:0 12px;outline:none}.locator-search button{height:40px;border:0;border-radius:12px;background:var(--red2);color:#fff;padding:0 14px;font-family:var(--mono);font-size:10px;letter-spacing:.07em;text-transform:uppercase;cursor:pointer}.locator-foot{margin-top:14px;padding-top:12px;border-top:1px solid var(--border);font-size:11px;line-height:1.55;color:var(--text3)}[data-theme="light"] .locator-state-card{background:rgba(255,255,255,.72)}[data-theme="light"] .state-locator-panel{background:linear-gradient(145deg,rgba(255,255,255,.92),rgba(255,255,255,.62));box-shadow:0 22px 60px rgba(29,78,216,.14)}
@media(max-width:800px){.locator-grid{grid-template-columns:1fr}.locator-actions{grid-template-columns:1fr}.hero-h1 span{border-radius:12px}.h1-l1::after,.h1-l2::after,.h1-l3::after{display:none}}

/* ──────────────────────────────────────────────
   TRUE FINAL HOTFIX — light-mode battleground overlay readability
   fixes invisible text inside the priority-state hover/tooltip area
   ────────────────────────────────────────────── */
[data-theme="light"] .globe-section{
  background:linear-gradient(180deg,#f8fbff 0%,#edf4ff 48%,#f8fbff 100%)!important;
}
[data-theme="light"] .globe-info,
[data-theme="light"] .globe-info *:not(.dot):not(.sc-dot){
  color:#0b1224!important;
}
[data-theme="light"] .globe-sub,
[data-theme="light"] .section-tag,
[data-theme="light"] .sc-ev{
  color:rgba(15,23,42,.68)!important;
}
[data-theme="light"] .globe-3d-wrap{
  background:linear-gradient(145deg,#ffffff 0%,#eaf1ff 58%,#dbe6f7 100%)!important;
  border:1px solid rgba(15,23,42,.12)!important;
  box-shadow:0 28px 80px rgba(15,23,42,.13), inset 0 1px 0 rgba(255,255,255,.95)!important;
}
[data-theme="light"] .bb-accurate-us-map rect{
  fill:rgba(255,255,255,.28)!important;
}
[data-theme="light"] .bb-accurate-us-map text{
  fill:#0b1224!important;
  stroke:rgba(255,255,255,.94)!important;
  stroke-width:3.25px!important;
  paint-order:stroke!important;
}
[data-theme="light"] .bb-state{
  stroke:rgba(255,255,255,.90)!important;
}
[data-theme="light"] #bg-map-tooltip.globe-tooltip{
  background:rgba(255,255,255,.97)!important;
  border:1px solid rgba(15,23,42,.16)!important;
  box-shadow:0 24px 70px rgba(15,23,42,.18)!important;
  color:#0b1224!important;
  opacity:0;
}
[data-theme="light"] #bg-map-tooltip.globe-tooltip.show{opacity:1!important}
[data-theme="light"] #bg-map-tooltip .tt-state{color:#0b1224!important}
[data-theme="light"] #bg-map-tooltip .tt-abbr,
[data-theme="light"] #bg-map-tooltip .tt-row{color:rgba(15,23,42,.68)!important}
[data-theme="light"] #bg-map-tooltip .tt-val{color:#0b1224!important}
[data-theme="light"] #bg-map-tooltip .tt-cta{
  color:#dc2626!important;
  border-top-color:rgba(15,23,42,.12)!important;
}
[data-theme="light"] .state-card{
  background:rgba(255,255,255,.92)!important;
  border-color:rgba(15,23,42,.12)!important;
}
[data-theme="light"] .state-card .sc-name{color:#0b1224!important}
[data-theme="light"] .state-card .sc-ev{color:rgba(15,23,42,.58)!important}
[data-theme="light"] .state-card .sc-status.sc-t-swing{color:#b45309!important}
[data-theme="light"] .state-card .sc-status.sc-t-lean-r{color:#dc2626!important}
[data-theme="light"] .state-card .sc-status.sc-t-lean-b{color:#2563eb!important}
[data-theme="light"] .legend .leg-chip{background:rgba(255,255,255,.72)!important}
[data-theme="light"] .leg-swing{color:#b45309!important;border-color:rgba(217,119,6,.32)!important}
[data-theme="light"] .leg-r{color:#dc2626!important;border-color:rgba(220,38,38,.26)!important}
[data-theme="light"] .leg-b{color:#2563eb!important;border-color:rgba(37,99,235,.28)!important}

</style>


<script id="vl-final-polish-js">
(function(){
  var GOV_LINKS={
    AL:'https://myinfo.alabamavotes.gov/',AK:'https://www.elections.alaska.gov/',AZ:'https://my.arizona.vote/',AR:'https://www.voterview.ar-nova.org/voterview',CA:'https://www.sos.ca.gov/elections/polling-place',CO:'https://www.sos.state.co.us/voter/pages/pub/olvr/findVoterReg.xhtml',CT:'https://portaldir.ct.gov/sots/LookUp.aspx',DE:'https://ivote.de.gov/',FL:'https://dos.myflorida.com/elections/for-voters/check-your-voter-status-and-polling-place/',GA:'https://mvp.sos.ga.gov/s/',HI:'https://olvr.hawaii.gov/',ID:'https://elections.sos.idaho.gov/ElectionLink/ElectionLink/VoterSearch.aspx',IL:'https://ova.elections.il.gov/pollingplacelookup.aspx',IN:'https://indianavoters.in.gov/',IA:'https://sos.iowa.gov/elections/voterreg/pollingplace/search.aspx',KS:'https://myvoteinfo.voteks.org/',KY:'https://vrsws.sos.ky.gov/vic/',LA:'https://voterportal.sos.la.gov/',ME:'https://www.maine.gov/sos/cec/elec/voter-info/voterguide.html',MD:'https://voterservices.elections.maryland.gov/',MA:'https://www.sec.state.ma.us/WhereDoIVoteMA/WhereDoIVote',MI:'https://mvic.sos.state.mi.us/',MN:'https://pollfinder.sos.state.mn.us/',MS:'https://www.sos.ms.gov/elections-voting/polling-place-locator',MO:'https://voteroutreach.sos.mo.gov/portal/',MT:'https://app.mt.gov/voterinfo/',NE:'https://www.votercheck.necvr.ne.gov/',NV:'https://www.nvsos.gov/votersearch/',NH:'https://app.sos.nh.gov/voterinformation',NJ:'https://voter.svrs.nj.gov/',NM:'https://voterportal.servis.sos.state.nm.us/WhereToVote.aspx',NY:'https://voterlookup.elections.ny.gov/',NC:'https://vt.ncsbe.gov/RegLkup/',ND:'https://vip.sos.nd.gov/WhereToVote.aspx',OH:'https://www.ohiosos.gov/elections/voters/toolkit/polling-location/',OK:'https://oklahoma.gov/elections/ovp.html',OR:'https://secure.sos.state.or.us/orestar/vr/showVoterSearch.do',PA:'https://www.pavoterservices.pa.gov/Pages/PollingPlaceInfo.aspx',RI:'https://vote.sos.ri.gov/',SC:'https://vrems.scvotes.sc.gov/Voter/Login',SD:'https://vip.sdsos.gov/viplogin.aspx',TN:'https://web.go-vote-tn.elections.tn.gov/',TX:'https://teamrv-mvp.sos.texas.gov/MVP/mvp.do',UT:'https://votesearch.utah.gov/voter-search/search/search-by-voter/voter-info',VT:'https://mvp.vermont.gov/',VA:'https://www.elections.virginia.gov/casting-a-ballot/polling-place-lookup/',WA:'https://voter.votewa.gov/portal2023/login.aspx',WV:'https://apps.sos.wv.gov/elections/voter/amiregisteredtovote',WI:'https://myvote.wi.gov/en-us/Find-My-Polling-Place',WY:'https://sos.wyo.gov/Elections/PollPlace/Default.aspx'
  };
  function st(abbr){return (window.STATES||[]).find(function(s){return s.a===abbr}) || {a:abbr,n:abbr};}
  function officialLinks(abbr){var name=st(abbr).n;return {poll:GOV_LINKS[abbr]||'https://www.usa.gov/state-election-office',mail:'https://www.usa.gov/state-election-office',register:'https://vote.gov/register/'+abbr.toLowerCase()+'/',eac:'https://www.eac.gov/voters/register-and-vote-in-your-state',vote:'https://vote.gov/'};}
  window.showStateLocator=function(abbr){
    var panel=document.getElementById('state-locator-panel');
    if(!panel)return;
    // Get state data
    var stateData=window.MAP_STATE_DATA&&MAP_STATE_DATA[abbr];
    var stateName=stateData?stateData.name:abbr;
    // Official, always-live government links
    var abbrL=abbr.toLowerCase();
    var links={
      register: 'https://vote.gov/register/'+abbrL+'/',
      eac:      'https://www.eac.gov/voters/register-and-vote-in-your-state',
      usagov:   'https://www.usa.gov/state-election-office',
      protection:'https://866ourvote.org/'
    };
    // State-specific SoS links for major states
    var sosLinks={
      GA:'https://mvp.sos.ga.gov/s/',AL:'https://www.alabamavotes.gov/',AK:'https://myvoterinformation.alaska.gov/',
      AZ:'https://my.arizona.vote/',AR:'https://www.sos.arkansas.gov/elections/',
      CA:'https://registertovote.ca.gov/',CO:'https://www.sos.state.co.us/voter/pages/pub/home.xhtml',
      CT:'https://myvote.ct.gov/',DE:'https://ivote.vote.org/voterregistration',
      FL:'https://registertovoteflorida.gov/',HI:'https://olvr.hawaii.gov/',
      ID:'https://idahovotes.gov/',IL:'https://www.elections.il.gov/',
      IN:'https://indianavoters.in.gov/',IA:'https://mymvd.iowadot.gov/Account/Login',
      KS:'https://www.kssos.org/elections/elections_registration.html',
      KY:'https://vrsws.sos.ky.gov/ovrweb/',LA:'https://voterportal.sos.la.gov/',
      ME:'https://www.maine.gov/sos/cec/elec/voter-info/voterguide.html',
      MD:'https://voterservices.elections.maryland.gov/OnlineVoterRegistration/',
      MA:'https://www.sec.state.ma.us/OVR/',MI:'https://mvic.sos.state.mi.us/',
      MN:'https://mnvotes.sos.state.mn.us/',MS:'https://www.sos.ms.gov/elections-voting/',
      MO:'https://www.sos.mo.gov/elections/goVoteMissouri/',MT:'https://app.mt.gov/voterinfo/',
      NE:'https://www.nebraska.gov/apps/voter/web/',NV:'https://www.nvsos.gov/sos/elections',
      NH:'https://app.sos.nh.gov/voterinformation/',NJ:'https://voter.svrs.nj.gov/register',
      NM:'https://portal.sos.state.nm.us/',NY:'https://www.elections.ny.gov/',
      NC:'https://www.ncsbe.gov/',ND:'https://vip.sos.nd.gov/',
      OH:'https://www.ohiosos.gov/elections/voters/',OK:'https://www.sos.ok.gov/elections/',
      OR:'https://sos.oregon.gov/voting/',PA:'https://www.vote.pa.gov/',
      RI:'https://vote.sos.ri.gov/',SC:'https://www.scvotes.gov/',
      SD:'https://sdsos.gov/elections-voting/',TN:'https://tnmap.tn.gov/voterlookup/',
      TX:'https://www.votetexas.gov/',UT:'https://vote.utah.gov/',
      VT:'https://olvr.vermont.gov/',VA:'https://www.elections.virginia.gov/',
      WA:'https://voter.votewa.gov/',WV:'https://ovr.sos.wv.gov/',
      WI:'https://myvote.wi.gov/',WY:'https://sos.wyo.gov/elections/',
      DC:'https://www.dcboe.org/'
    };
    var sosLink=sosLinks[abbr]||links.register;
    // State info
    var reg   = stateData?stateData.reg  :'Check your state election website';
    var id    = stateData?stateData.id   :'Check your state election website';
    var early = stateData?stateData.early:'Check your state election website';
    var mail  = stateData?stateData.absentee:'Check your state election website';
    var lean  = stateData?stateData.lean :'';
    var leanLabels={'solid-r':'Republican','lean-r':'Leans Republican','swing':'Battleground','lean-b':'Leans Democrat','solid-b':'Democrat'};

    panel.classList.add('open');
    panel.innerHTML=
      '<button class="locator-close" type="button" onclick="window.closeStateLocator&&closeStateLocator()" aria-label="Close">\xd7</button>'+
      '<div class="locator-grid">'+
        '<div class="locator-state-card">'+
          '<div class="locator-kicker">'+stateName+' Voting Information</div>'+
          '<div class="locator-name">'+stateName+'</div>'+
          '<div class="locator-facts">'+
            '<div class="lf-row"><span class="lf-label">Registration deadline</span><span class="lf-val">'+reg+'</span></div>'+
            '<div class="lf-row"><span class="lf-label">Voter ID requirement</span><span class="lf-val">'+id+'</span></div>'+
            '<div class="lf-row"><span class="lf-label">Early voting</span><span class="lf-val">'+early+'</span></div>'+
            '<div class="lf-row"><span class="lf-label">Mail-in / Absentee</span><span class="lf-val">'+mail+'</span></div>'+
            (lean?'<div class="lf-row"><span class="lf-label">Political lean</span><span class="lf-val">'+(leanLabels[lean]||lean)+'</span></div>':'')+
          '</div>'+
          '<div class="locator-foot"><strong>Important:</strong> Deadlines vary by county and election. Always confirm at your official state election website before Election Day.</div>'+
        '</div>'+
        '<div>'+
          '<div class="locator-trust">Official Government Sources</div>'+
          '<div class="locator-actions">'+
            '<a class="locator-btn" href="'+sosLink+'" target="_blank" rel="noopener"><span>\ud83c\udfe7</span><div><strong>'+stateName+' Elections Office</strong><small>Official Secretary of State voter registration and election information.</small></div></a>'+
            '<a class="locator-btn" href="'+links.register+'" target="_blank" rel="noopener"><span>\ud83d\udcdd</span><div><strong>Register at Vote.gov</strong><small>Federal portal for '+stateName+' voter registration.</small></div></a>'+
            '<a class="locator-btn" href="'+links.eac+'" target="_blank" rel="noopener"><span>\ud83d\udee1\ufe0f</span><div><strong>U.S. Election Assistance Commission</strong><small>Federal nonpartisan voter information for '+stateName+'.</small></div></a>'+
            '<a class="locator-btn" href="'+links.protection+'" target="_blank" rel="noopener"><span>\ud83d\udcde</span><div><strong>866-OUR-VOTE Hotline</strong><small>Free nonpartisan legal help for any voting problem.</small></div></a>'+
          '</div>'+
          '<div class="locator-foot">All links go directly to official .gov or verified nonprofit sites. VoterLens never uses third-party or unofficial sources.</div>'+
          '<div style="margin-top:14px"><button class="mc-btn" style="width:100%" onclick="window.closeStateLocator&&closeStateLocator();window.goPage&&goPage(\'chat\');setTimeout(function(){var ta=document.getElementById(\'chat-ta\');if(ta){ta.value=\'What are the full voting requirements and registration steps for '+stateName.replace(/'/g,"\\'")+'?\';window.sendMsg&&sendMsg();}},100)">Ask VoterLens about '+stateName+' \u2192</button></div>'+
        '</div>'+
      '</div>';
    panel.scrollIntoView({behavior:'smooth',block:'nearest'});
    try{if(typeof earnBadge==='function')earnBadge('state');}catch(e){}
  };
    if(document.getElementById('chat-state')) document.getElementById('chat-state').value=abbr;
    if(typeof goPage==='function') goPage('chat');
    setTimeout(function(){var ta=document.getElementById('chat-ta'); if(ta){ta.value='Help me find official polling-place and election-office mailing-location resources for '+s.n+(z.trim()?(' using this ZIP/county note: '+z.trim()):'')+'. Only use government sources.'; if(typeof sendMsg==='function') sendMsg();}},120);
  };
  document.addEventListener('click',function(e){
    var state=e.target.closest && e.target.closest('.bb-state');
    if(state){var m=(state.getAttribute('class')||'').match(/bb-state-([A-Z]{2})/); if(m){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();showStateLocator(m[1]);return false;}}
  },true);
  document.addEventListener('DOMContentLoaded',function(){
    var ta=document.getElementById('chat-ta'); if(ta) ta.placeholder='Ask about deadlines, ID, mail ballots, polling locations, rights at the polls, or local election offices...';
    var grid=document.getElementById('state-cards'); if(grid){grid.querySelectorAll('.state-card').forEach(function(card){var name=(card.querySelector('.sc-name')||{}).textContent;var found=(window.STATES||[]).find(function(s){return s.n===name}); if(found){card.setAttribute('data-abbr',found.a);card.onclick=function(ev){ev.preventDefault();showStateLocator(found.a);};}})}
    if(window.BADGE_DEFS){
      window.BADGE_DEFS=[
        {id:'firstask',icon:'💬',name:'First Question Asked',desc:'You asked VoterLens your first voting question.',action:'Ask a question in the chat'},
        {id:'plan',icon:'📋',name:'Voting Plan Built',desc:'You created a personalized voting plan.',action:'Build your voting plan'},
        {id:'state',icon:'🗺️',name:'State Explorer',desc:'You expanded a state for official voting-location help.',action:'Touch any state on the map'},
        {id:'locator',icon:'📍',name:'Polling Place Ready',desc:'You opened official polling-place lookup resources.',action:'Use the state locator'},
        {id:'mail',icon:'✉️',name:'Mailing Office Finder',desc:'You learned where to find election-office mailing locations.',action:'Open mailing-location help'},
        {id:'timeline',icon:'📜',name:'History Seeker',desc:'You explored the Democracy Timeline.',action:'Visit the History page'},
        {id:'emer',icon:'🚨',name:'Rights Defender',desc:'You learned what to do if something goes wrong at the polls.',action:'Open Emergency Help'},
        {id:'sources',icon:'🛡️',name:'Source Checker',desc:'You clicked an official government source link.',action:'Click a source link'},
        {id:'chat5',icon:'🎓',name:'Civic Learner',desc:'You asked five voting questions.',action:'Ask 5 questions'},
        {id:'map',icon:'🌟',name:'Democracy Researcher',desc:'You explored three different states.',action:'Explore 3 states'},
        {id:'idrules',icon:'🪪',name:'ID Rule Reviewer',desc:'You reviewed voter ID requirements.',action:'Ask about voter ID'},
        {id:'mailballot',icon:'📫',name:'Mail Ballot Planner',desc:'You checked mail/absentee ballot steps.',action:'Ask about mail ballots'}
      ];
      if(typeof initBadges==='function') initBadges();
    }
  });
  var oldShow=window.showStateLocator;
  window.showStateLocator=function(abbr){oldShow(abbr);try{earnBadge('locator');}catch(e){}};
})();
</script>



<!-- FINAL FIX: cleaner hero lines + working 50-state polling/mailing expansion -->
<style id="vl-state-expansion-final-fix">
/* Clean the hero statement so it reads as three polished lines, not huge boxed rows */
.hero{align-items:center!important;padding-top:clamp(72px,9vh,112px)!important}
.hero-inner{max-width:min(620px,92vw)!important}
.hero-h1{
  display:flex!important;flex-direction:column!important;gap:4px!important;align-items:flex-start!important;
  font-size:clamp(42px,5.4vw,78px)!important;line-height:.98!important;margin-bottom:18px!important;
  letter-spacing:-.035em!important;overflow:visible!important;
}
.hero-h1 span{
  display:block!important;width:auto!important;max-width:100%!important;padding:0!important;margin:0!important;
  background:transparent!important;border:0!important;border-radius:0!important;box-shadow:none!important;
  line-height:.98!important;white-space:nowrap!important;
}
.h1-l1::after,.h1-l2::after,.h1-l3::after{display:none!important;content:none!important}
.h1-l1{color:var(--text)!important;text-shadow:0 18px 44px rgba(0,0,0,.24)!important}
.h1-l2{color:var(--red2)!important;text-shadow:0 0 34px rgba(220,38,38,.38)!important}
.h1-l3{color:#1d4ed8!important;-webkit-text-stroke:0!important;text-shadow:0 0 36px rgba(29,78,216,.36)!important}
[data-theme="light"] .h1-l1{color:#0b1220!important;text-shadow:0 12px 28px rgba(13,21,38,.10)!important}
[data-theme="light"] .h1-l2{color:#dc2626!important;text-shadow:0 10px 26px rgba(220,38,38,.12)!important}
[data-theme="light"] .h1-l3{color:#1d4ed8!important;text-shadow:0 10px 26px rgba(29,78,216,.14)!important}
.hero-desc{margin-top:16px!important;max-width:430px!important}
@media(max-width:720px){.hero-h1{font-size:clamp(40px,12vw,64px)!important}.hero-h1 span{white-space:normal!important}}

/* Make the map state expansion feel intentional and clickable */
.map-stage{overflow:visible!important;isolation:isolate!important}
.map-stage::after{
  content:"Tap a state to expand official polling + mailing help";position:absolute;left:18px;bottom:16px;z-index:6;
  font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--text2);
  padding:8px 12px;border-radius:999px;border:1px solid var(--border);background:rgba(5,12,30,.72);backdrop-filter:blur(12px);
}
[data-theme="light"] .map-stage::after{background:rgba(255,255,255,.82);color:rgba(13,21,38,.62)}
.bb-state{cursor:pointer!important;transition:transform .18s ease,filter .18s ease,stroke-width .18s ease!important;transform-box:fill-box;transform-origin:center}
.bb-state:hover{transform:translateY(-5px) scale(1.018)!important;filter:drop-shadow(0 16px 22px rgba(96,165,250,.35)) brightness(1.12)!important;stroke-width:2.4!important}
.bb-state.bb-selected{transform:translateY(-8px) scale(1.025)!important;filter:drop-shadow(0 22px 32px rgba(245,158,11,.35)) brightness(1.18)!important;stroke:#f59e0b!important;stroke-width:2.8!important}
.state-locator-panel{scroll-margin-top:90px!important;position:relative!important}
.state-locator-panel.open{animation:locatorPop .36s cubic-bezier(.22,1,.36,1) both;border-color:rgba(245,158,11,.35)!important;box-shadow:0 28px 90px rgba(0,0,0,.34),0 0 0 1px rgba(245,158,11,.08)!important}
@keyframes locatorPop{from{opacity:.45;transform:translateY(16px) scale(.985)}to{opacity:1;transform:none}}
.locator-close{position:absolute;right:14px;top:14px;width:32px;height:32px;border-radius:10px;border:1px solid var(--border);background:var(--surface);color:var(--text2);cursor:pointer;font-size:18px;z-index:3}
.locator-close:hover{background:var(--surface2);color:var(--text)}
.locator-mini-map{position:absolute;right:18px;top:18px;font-family:var(--serif);font-size:58px;font-weight:900;color:rgba(245,158,11,.16);line-height:1;pointer-events:none}
.locator-actions{grid-template-columns:repeat(2,minmax(0,1fr))!important}
.locator-btn.primary{background:linear-gradient(135deg,rgba(220,38,38,.18),rgba(245,158,11,.08))!important;border-color:rgba(220,38,38,.34)!important}
.locator-btn.primary strong{color:#fff}
[data-theme="light"] .locator-btn.primary strong{color:#0d1526}
.locator-warning{margin-top:12px;padding:12px;border-radius:14px;background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.22);font-size:12px;line-height:1.55;color:var(--text2)}
.locator-source-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.locator-source-pill{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;border:1px solid var(--border);background:var(--surface);font-family:var(--mono);font-size:9.5px;color:var(--text2)}
@media(max-width:800px){.locator-actions{grid-template-columns:1fr!important}.map-stage::after{left:12px;right:12px;text-align:center}.locator-mini-map{display:none}}

/* ──────────────────────────────────────────────
   TRUE FINAL HOTFIX — light-mode battleground overlay readability
   fixes invisible text inside the priority-state hover/tooltip area
   ────────────────────────────────────────────── */
[data-theme="light"] .globe-section{
  background:linear-gradient(180deg,#f8fbff 0%,#edf4ff 48%,#f8fbff 100%)!important;
}
[data-theme="light"] .globe-info,
[data-theme="light"] .globe-info *:not(.dot):not(.sc-dot){
  color:#0b1224!important;
}
[data-theme="light"] .globe-sub,
[data-theme="light"] .section-tag,
[data-theme="light"] .sc-ev{
  color:rgba(15,23,42,.68)!important;
}
[data-theme="light"] .globe-3d-wrap{
  background:linear-gradient(145deg,#ffffff 0%,#eaf1ff 58%,#dbe6f7 100%)!important;
  border:1px solid rgba(15,23,42,.12)!important;
  box-shadow:0 28px 80px rgba(15,23,42,.13), inset 0 1px 0 rgba(255,255,255,.95)!important;
}
[data-theme="light"] .bb-accurate-us-map rect{
  fill:rgba(255,255,255,.28)!important;
}
[data-theme="light"] .bb-accurate-us-map text{
  fill:#0b1224!important;
  stroke:rgba(255,255,255,.94)!important;
  stroke-width:3.25px!important;
  paint-order:stroke!important;
}
[data-theme="light"] .bb-state{
  stroke:rgba(255,255,255,.90)!important;
}
[data-theme="light"] #bg-map-tooltip.globe-tooltip{
  background:rgba(255,255,255,.97)!important;
  border:1px solid rgba(15,23,42,.16)!important;
  box-shadow:0 24px 70px rgba(15,23,42,.18)!important;
  color:#0b1224!important;
  opacity:0;
}
[data-theme="light"] #bg-map-tooltip.globe-tooltip.show{opacity:1!important}
[data-theme="light"] #bg-map-tooltip .tt-state{color:#0b1224!important}
[data-theme="light"] #bg-map-tooltip .tt-abbr,
[data-theme="light"] #bg-map-tooltip .tt-row{color:rgba(15,23,42,.68)!important}
[data-theme="light"] #bg-map-tooltip .tt-val{color:#0b1224!important}
[data-theme="light"] #bg-map-tooltip .tt-cta{
  color:#dc2626!important;
  border-top-color:rgba(15,23,42,.12)!important;
}
[data-theme="light"] .state-card{
  background:rgba(255,255,255,.92)!important;
  border-color:rgba(15,23,42,.12)!important;
}
[data-theme="light"] .state-card .sc-name{color:#0b1224!important}
[data-theme="light"] .state-card .sc-ev{color:rgba(15,23,42,.58)!important}
[data-theme="light"] .state-card .sc-status.sc-t-swing{color:#b45309!important}
[data-theme="light"] .state-card .sc-status.sc-t-lean-r{color:#dc2626!important}
[data-theme="light"] .state-card .sc-status.sc-t-lean-b{color:#2563eb!important}
[data-theme="light"] .legend .leg-chip{background:rgba(255,255,255,.72)!important}
[data-theme="light"] .leg-swing{color:#b45309!important;border-color:rgba(217,119,6,.32)!important}
[data-theme="light"] .leg-r{color:#dc2626!important;border-color:rgba(220,38,38,.26)!important}
[data-theme="light"] .leg-b{color:#2563eb!important;border-color:rgba(37,99,235,.28)!important}

</style>


<style id="vl-polish-final-visual-fixes">
/* FINAL POLISH: remove the floating oval, make maps/globes prettier, and clean hero lines */
:root{--bb-hero-cream:#fff7ed;--bb-hero-blue:#2563eb;--bb-panel-glass:rgba(5,12,30,.72)}
[data-theme="light"]{
  --bg:#f7faff;--bg2:#eef4ff;--bg3:#e7efff;
  --surface:rgba(255,255,255,.76);--surface2:rgba(255,255,255,.94);
  --border:rgba(30,64,120,.14);--border2:rgba(30,64,120,.24);
  --text:#0b1730;--text2:rgba(11,23,48,.72);--text3:rgba(11,23,48,.46);
}
[data-theme="light"] body{background:radial-gradient(circle at 20% 12%,rgba(96,165,250,.20),transparent 34%),radial-gradient(circle at 78% 22%,rgba(220,38,38,.08),transparent 28%),linear-gradient(135deg,#f9fbff 0%,#eef4ff 52%,#e8f0ff 100%)}
[data-theme="light"] .bg-overlay{background:radial-gradient(ellipse 70% 58% at 50% 38%,transparent 0%,rgba(247,250,255,.72) 72%,rgba(247,250,255,.96) 100%)}
[data-theme="light"] nav{background:rgba(255,255,255,.78);box-shadow:0 12px 36px rgba(30,64,120,.08)}
.hero-inner{max-width:min(760px,100%)}
.hero-h1{display:grid;gap:12px;margin-bottom:18px;font-size:clamp(40px,6.4vw,88px);line-height:.88;letter-spacing:-.035em;max-width:720px}
.hero-h1 span{display:block;width:max-content;max-width:100%;padding:.055em .16em .105em;border-radius:22px;background:linear-gradient(90deg,rgba(255,255,255,.045),rgba(255,255,255,.012));border:1px solid rgba(255,255,255,.075);box-shadow:inset 0 1px 0 rgba(255,255,255,.07)}
.h1-l1{color:var(--bb-hero-cream)!important}.h1-l2{color:#ef2b2d!important}.h1-l3{color:#2563eb!important;-webkit-text-stroke:0!important;text-shadow:0 0 38px rgba(37,99,235,.28)}
[data-theme="light"] .hero-h1 span{background:rgba(255,255,255,.74);border-color:rgba(30,64,120,.13);box-shadow:0 16px 40px rgba(30,64,120,.08),inset 0 1px 0 rgba(255,255,255,.9)}
[data-theme="light"] .h1-l1{color:#0b1730!important}.hero-desc{font-size:clamp(15px,1.7vw,18px)}
/* Kill the weird floating/oval ornament on the USA map */
.map-stage::after{display:none!important;content:none!important}
.map-stage::before{inset:10px;border-radius:18px;border-color:rgba(96,165,250,.14);box-shadow:inset 0 0 50px rgba(96,165,250,.08),0 0 40px rgba(37,99,235,.10)}
.map-stage{background:radial-gradient(circle at 48% 42%,rgba(37,99,235,.22),transparent 38%),linear-gradient(145deg,rgba(4,12,28,.96),rgba(10,24,50,.88))!important;border:1px solid rgba(148,163,184,.18)!important;box-shadow:0 38px 120px rgba(0,0,0,.62),0 0 60px rgba(37,99,235,.12),inset 0 1px 0 rgba(255,255,255,.08)!important;overflow:hidden}
[data-theme="light"] .map-stage{background:radial-gradient(circle at 48% 42%,rgba(37,99,235,.16),transparent 42%),linear-gradient(145deg,rgba(255,255,255,.98),rgba(230,239,255,.88))!important;border-color:rgba(37,99,235,.16)!important;box-shadow:0 30px 85px rgba(30,64,120,.16),0 0 0 1px rgba(255,255,255,.8),inset 0 1px 0 rgba(255,255,255,.95)!important}
#map-canvas,.bb-map-svg{filter:drop-shadow(0 28px 32px rgba(0,0,0,.35)) saturate(1.12)}
[data-theme="light"] #map-canvas,[data-theme="light"] .bb-map-svg{filter:drop-shadow(0 24px 26px rgba(30,64,120,.20)) saturate(1.05)}
.bb-state{transition:filter .2s ease,transform .2s ease,stroke-width .2s ease;filter:drop-shadow(0 3px 2px rgba(0,0,0,.22))}.bb-state:hover,.bb-state.bb-selected{filter:drop-shadow(0 0 14px rgba(245,158,11,.65)) drop-shadow(0 10px 10px rgba(0,0,0,.25));stroke:#fff7ed!important;stroke-width:2.2!important}
[data-theme="light"] .bb-state:hover,[data-theme="light"] .bb-state.bb-selected{filter:drop-shadow(0 0 12px rgba(220,38,38,.35)) drop-shadow(0 12px 12px rgba(30,64,120,.16));stroke:#0b1730!important}
.globe-wrap,.globe-3d-wrap{pointer-events:auto!important;cursor:grab;filter:drop-shadow(0 30px 48px rgba(0,0,0,.42)) drop-shadow(0 0 44px rgba(37,99,235,.22))}.globe-wrap:active,.globe-3d-wrap:active{cursor:grabbing}
[data-theme="light"] .globe-wrap,[data-theme="light"] .globe-3d-wrap{filter:drop-shadow(0 28px 40px rgba(30,64,120,.22)) drop-shadow(0 0 38px rgba(37,99,235,.18))}
.globe-wrap::after,.globe-3d-wrap::after{border-color:rgba(96,165,250,.25);box-shadow:0 0 42px rgba(37,99,235,.14)}
.state-locator-panel.open{border-color:rgba(245,158,11,.28);box-shadow:0 28px 90px rgba(0,0,0,.32),0 0 42px rgba(245,158,11,.08)}
[data-theme="light"] .state-locator-panel.open{background:rgba(255,255,255,.86);box-shadow:0 24px 70px rgba(30,64,120,.14)}
.locator-state-card{background:linear-gradient(145deg,rgba(255,255,255,.07),rgba(96,165,250,.06));border:1px solid var(--border);border-radius:22px;padding:22px;position:relative;overflow:hidden}
[data-theme="light"] .locator-state-card{background:linear-gradient(145deg,rgba(255,255,255,.96),rgba(239,246,255,.82))}
@media(max-width:760px){.hero-h1{font-size:clamp(38px,14vw,62px);gap:10px}.hero-h1 span{border-radius:16px}.hero{padding-top:36px}}

/* ──────────────────────────────────────────────
   TRUE FINAL HOTFIX — light-mode battleground overlay readability
   fixes invisible text inside the priority-state hover/tooltip area
   ────────────────────────────────────────────── */
[data-theme="light"] .globe-section{
  background:linear-gradient(180deg,#f8fbff 0%,#edf4ff 48%,#f8fbff 100%)!important;
}
[data-theme="light"] .globe-info,
[data-theme="light"] .globe-info *:not(.dot):not(.sc-dot){
  color:#0b1224!important;
}
[data-theme="light"] .globe-sub,
[data-theme="light"] .section-tag,
[data-theme="light"] .sc-ev{
  color:rgba(15,23,42,.68)!important;
}
[data-theme="light"] .globe-3d-wrap{
  background:linear-gradient(145deg,#ffffff 0%,#eaf1ff 58%,#dbe6f7 100%)!important;
  border:1px solid rgba(15,23,42,.12)!important;
  box-shadow:0 28px 80px rgba(15,23,42,.13), inset 0 1px 0 rgba(255,255,255,.95)!important;
}
[data-theme="light"] .bb-accurate-us-map rect{
  fill:rgba(255,255,255,.28)!important;
}
[data-theme="light"] .bb-accurate-us-map text{
  fill:#0b1224!important;
  stroke:rgba(255,255,255,.94)!important;
  stroke-width:3.25px!important;
  paint-order:stroke!important;
}
[data-theme="light"] .bb-state{
  stroke:rgba(255,255,255,.90)!important;
}
[data-theme="light"] #bg-map-tooltip.globe-tooltip{
  background:rgba(255,255,255,.97)!important;
  border:1px solid rgba(15,23,42,.16)!important;
  box-shadow:0 24px 70px rgba(15,23,42,.18)!important;
  color:#0b1224!important;
  opacity:0;
}
[data-theme="light"] #bg-map-tooltip.globe-tooltip.show{opacity:1!important}
[data-theme="light"] #bg-map-tooltip .tt-state{color:#0b1224!important}
[data-theme="light"] #bg-map-tooltip .tt-abbr,
[data-theme="light"] #bg-map-tooltip .tt-row{color:rgba(15,23,42,.68)!important}
[data-theme="light"] #bg-map-tooltip .tt-val{color:#0b1224!important}
[data-theme="light"] #bg-map-tooltip .tt-cta{
  color:#dc2626!important;
  border-top-color:rgba(15,23,42,.12)!important;
}
[data-theme="light"] .state-card{
  background:rgba(255,255,255,.92)!important;
  border-color:rgba(15,23,42,.12)!important;
}
[data-theme="light"] .state-card .sc-name{color:#0b1224!important}
[data-theme="light"] .state-card .sc-ev{color:rgba(15,23,42,.58)!important}
[data-theme="light"] .state-card .sc-status.sc-t-swing{color:#b45309!important}
[data-theme="light"] .state-card .sc-status.sc-t-lean-r{color:#dc2626!important}
[data-theme="light"] .state-card .sc-status.sc-t-lean-b{color:#2563eb!important}
[data-theme="light"] .legend .leg-chip{background:rgba(255,255,255,.72)!important}
[data-theme="light"] .leg-swing{color:#b45309!important;border-color:rgba(217,119,6,.32)!important}
[data-theme="light"] .leg-r{color:#dc2626!important;border-color:rgba(220,38,38,.26)!important}
[data-theme="light"] .leg-b{color:#2563eb!important;border-color:rgba(37,99,235,.28)!important}

</style>

<script id="vl-state-expansion-final-fix-js">
(function(){
  var POLLING_LINKS={
    AL:'https://myinfo.alabamavotes.gov/',AK:'https://www.elections.alaska.gov/',AZ:'https://my.arizona.vote/',AR:'https://www.voterview.ar-nova.org/voterview',CA:'https://www.sos.ca.gov/elections/polling-place',CO:'https://www.sos.state.co.us/voter/pages/pub/olvr/findVoterReg.xhtml',CT:'https://portaldir.ct.gov/sots/LookUp.aspx',DE:'https://ivote.de.gov/',FL:'https://dos.myflorida.com/elections/for-voters/check-your-voter-status-and-polling-place/',GA:'https://mvp.sos.ga.gov/s/',HI:'https://olvr.hawaii.gov/',ID:'https://elections.sos.idaho.gov/ElectionLink/ElectionLink/VoterSearch.aspx',IL:'https://ova.elections.il.gov/pollingplacelookup.aspx',IN:'https://indianavoters.in.gov/',IA:'https://sos.iowa.gov/elections/voterreg/pollingplace/search.aspx',KS:'https://myvoteinfo.voteks.org/',KY:'https://vrsws.sos.ky.gov/vic/',LA:'https://voterportal.sos.la.gov/',ME:'https://www.maine.gov/sos/cec/elec/voter-info/voterguide.html',MD:'https://voterservices.elections.maryland.gov/',MA:'https://www.sec.state.ma.us/WhereDoIVoteMA/WhereDoIVote',MI:'https://mvic.sos.state.mi.us/',MN:'https://pollfinder.sos.state.mn.us/',MS:'https://www.sos.ms.gov/elections-voting/polling-place-locator',MO:'https://voteroutreach.sos.mo.gov/portal/',MT:'https://app.mt.gov/voterinfo/',NE:'https://www.votercheck.necvr.ne.gov/',NV:'https://www.nvsos.gov/votersearch/',NH:'https://app.sos.nh.gov/voterinformation',NJ:'https://voter.svrs.nj.gov/',NM:'https://voterportal.servis.sos.state.nm.us/WhereToVote.aspx',NY:'https://voterlookup.elections.ny.gov/',NC:'https://vt.ncsbe.gov/RegLkup/',ND:'https://vip.sos.nd.gov/WhereToVote.aspx',OH:'https://www.ohiosos.gov/elections/voters/toolkit/polling-location/',OK:'https://oklahoma.gov/elections/ovp.html',OR:'https://secure.sos.state.or.us/orestar/vr/showVoterSearch.do',PA:'https://www.pavoterservices.pa.gov/Pages/PollingPlaceInfo.aspx',RI:'https://vote.sos.ri.gov/',SC:'https://vrems.scvotes.sc.gov/Voter/Login',SD:'https://vip.sdsos.gov/viplogin.aspx',TN:'https://web.go-vote-tn.elections.tn.gov/',TX:'https://teamrv-mvp.sos.texas.gov/MVP/mvp.do',UT:'https://votesearch.utah.gov/voter-search/search/search-by-voter/voter-info',VT:'https://mvp.vermont.gov/',VA:'https://www.elections.virginia.gov/casting-a-ballot/polling-place-lookup/',WA:'https://voter.votewa.gov/portal2023/login.aspx',WV:'https://apps.sos.wv.gov/elections/voter/amiregisteredtovote',WI:'https://myvote.wi.gov/en-us/Find-My-Polling-Place',WY:'https://sos.wyo.gov/Elections/PollPlace/Default.aspx'
  };
  function ready(fn){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',fn);else fn();}
  function stateObj(abbr){return (window.STATES||[]).find(function(s){return s.a===abbr})||{a:abbr,n:abbr};}
  function linkSet(abbr){return {
    poll:POLLING_LINKS[abbr]||'https://www.usa.gov/state-election-office',
    mail:'https://www.usa.gov/state-election-office',
    register:'https://vote.gov/register/'+String(abbr).toLowerCase()+'/',
    eac:'https://www.eac.gov/voters/register-and-vote-in-your-state',
    vote:'https://vote.gov/'
  };}
  function setHeroPeriods(){['.h1-l1','.h1-l2','.h1-l3'].forEach(function(sel){var el=document.querySelector(sel);if(el && !/[.!?]$/.test(el.textContent.trim())) el.textContent=el.textContent.trim()+'.';});}
  window.closeStateLocator=function(){var panel=document.getElementById('state-locator-panel');if(panel){panel.classList.remove('open');panel.innerHTML='<div class="locator-empty"><div class="locator-kicker">50-state expansion ready</div><h3>Touch any state on the map.</h3><p>The panel will expand with official polling-place lookup, mailing-office help, registration instructions, and EAC verification.</p></div>';}document.querySelectorAll('.bb-state').forEach(function(p){p.classList.remove('bb-selected');});};
  window.showStateLocator=function(abbr){
    var panel=document.getElementById('state-locator-panel');
    if(!panel)return;
    // Get state data
    var stateData=window.MAP_STATE_DATA&&MAP_STATE_DATA[abbr];
    var stateName=stateData?stateData.name:abbr;
    // Official, always-live government links
    var abbrL=abbr.toLowerCase();
    var links={
      register: 'https://vote.gov/register/'+abbrL+'/',
      eac:      'https://www.eac.gov/voters/register-and-vote-in-your-state',
      usagov:   'https://www.usa.gov/state-election-office',
      protection:'https://866ourvote.org/'
    };
    // State-specific SoS links for major states
    var sosLinks={
      GA:'https://mvp.sos.ga.gov/s/',AL:'https://www.alabamavotes.gov/',AK:'https://myvoterinformation.alaska.gov/',
      AZ:'https://my.arizona.vote/',AR:'https://www.sos.arkansas.gov/elections/',
      CA:'https://registertovote.ca.gov/',CO:'https://www.sos.state.co.us/voter/pages/pub/home.xhtml',
      CT:'https://myvote.ct.gov/',DE:'https://ivote.vote.org/voterregistration',
      FL:'https://registertovoteflorida.gov/',HI:'https://olvr.hawaii.gov/',
      ID:'https://idahovotes.gov/',IL:'https://www.elections.il.gov/',
      IN:'https://indianavoters.in.gov/',IA:'https://mymvd.iowadot.gov/Account/Login',
      KS:'https://www.kssos.org/elections/elections_registration.html',
      KY:'https://vrsws.sos.ky.gov/ovrweb/',LA:'https://voterportal.sos.la.gov/',
      ME:'https://www.maine.gov/sos/cec/elec/voter-info/voterguide.html',
      MD:'https://voterservices.elections.maryland.gov/OnlineVoterRegistration/',
      MA:'https://www.sec.state.ma.us/OVR/',MI:'https://mvic.sos.state.mi.us/',
      MN:'https://mnvotes.sos.state.mn.us/',MS:'https://www.sos.ms.gov/elections-voting/',
      MO:'https://www.sos.mo.gov/elections/goVoteMissouri/',MT:'https://app.mt.gov/voterinfo/',
      NE:'https://www.nebraska.gov/apps/voter/web/',NV:'https://www.nvsos.gov/sos/elections',
      NH:'https://app.sos.nh.gov/voterinformation/',NJ:'https://voter.svrs.nj.gov/register',
      NM:'https://portal.sos.state.nm.us/',NY:'https://www.elections.ny.gov/',
      NC:'https://www.ncsbe.gov/',ND:'https://vip.sos.nd.gov/',
      OH:'https://www.ohiosos.gov/elections/voters/',OK:'https://www.sos.ok.gov/elections/',
      OR:'https://sos.oregon.gov/voting/',PA:'https://www.vote.pa.gov/',
      RI:'https://vote.sos.ri.gov/',SC:'https://www.scvotes.gov/',
      SD:'https://sdsos.gov/elections-voting/',TN:'https://tnmap.tn.gov/voterlookup/',
      TX:'https://www.votetexas.gov/',UT:'https://vote.utah.gov/',
      VT:'https://olvr.vermont.gov/',VA:'https://www.elections.virginia.gov/',
      WA:'https://voter.votewa.gov/',WV:'https://ovr.sos.wv.gov/',
      WI:'https://myvote.wi.gov/',WY:'https://sos.wyo.gov/elections/',
      DC:'https://www.dcboe.org/'
    };
    var sosLink=sosLinks[abbr]||links.register;
    // State info
    var reg   = stateData?stateData.reg  :'Check your state election website';
    var id    = stateData?stateData.id   :'Check your state election website';
    var early = stateData?stateData.early:'Check your state election website';
    var mail  = stateData?stateData.absentee:'Check your state election website';
    var lean  = stateData?stateData.lean :'';
    var leanLabels={'solid-r':'Republican','lean-r':'Leans Republican','swing':'Battleground','lean-b':'Leans Democrat','solid-b':'Democrat'};

    panel.classList.add('open');
    panel.innerHTML=
      '<button class="locator-close" type="button" onclick="window.closeStateLocator&&closeStateLocator()" aria-label="Close">\xd7</button>'+
      '<div class="locator-grid">'+
        '<div class="locator-state-card">'+
          '<div class="locator-kicker">'+stateName+' Voting Information</div>'+
          '<div class="locator-name">'+stateName+'</div>'+
          '<div class="locator-facts">'+
            '<div class="lf-row"><span class="lf-label">Registration deadline</span><span class="lf-val">'+reg+'</span></div>'+
            '<div class="lf-row"><span class="lf-label">Voter ID requirement</span><span class="lf-val">'+id+'</span></div>'+
            '<div class="lf-row"><span class="lf-label">Early voting</span><span class="lf-val">'+early+'</span></div>'+
            '<div class="lf-row"><span class="lf-label">Mail-in / Absentee</span><span class="lf-val">'+mail+'</span></div>'+
            (lean?'<div class="lf-row"><span class="lf-label">Political lean</span><span class="lf-val">'+(leanLabels[lean]||lean)+'</span></div>':'')+
          '</div>'+
          '<div class="locator-foot"><strong>Important:</strong> Deadlines vary by county and election. Always confirm at your official state election website before Election Day.</div>'+
        '</div>'+
        '<div>'+
          '<div class="locator-trust">Official Government Sources</div>'+
          '<div class="locator-actions">'+
            '<a class="locator-btn" href="'+sosLink+'" target="_blank" rel="noopener"><span>\ud83c\udfe7</span><div><strong>'+stateName+' Elections Office</strong><small>Official Secretary of State voter registration and election information.</small></div></a>'+
            '<a class="locator-btn" href="'+links.register+'" target="_blank" rel="noopener"><span>\ud83d\udcdd</span><div><strong>Register at Vote.gov</strong><small>Federal portal for '+stateName+' voter registration.</small></div></a>'+
            '<a class="locator-btn" href="'+links.eac+'" target="_blank" rel="noopener"><span>\ud83d\udee1\ufe0f</span><div><strong>U.S. Election Assistance Commission</strong><small>Federal nonpartisan voter information for '+stateName+'.</small></div></a>'+
            '<a class="locator-btn" href="'+links.protection+'" target="_blank" rel="noopener"><span>\ud83d\udcde</span><div><strong>866-OUR-VOTE Hotline</strong><small>Free nonpartisan legal help for any voting problem.</small></div></a>'+
          '</div>'+
          '<div class="locator-foot">All links go directly to official .gov or verified nonprofit sites. VoterLens never uses third-party or unofficial sources.</div>'+
          '<div style="margin-top:14px"><button class="mc-btn" style="width:100%" onclick="window.closeStateLocator&&closeStateLocator();window.goPage&&goPage(\'chat\');setTimeout(function(){var ta=document.getElementById(\'chat-ta\');if(ta){ta.value=\'What are the full voting requirements and registration steps for '+stateName.replace(/'/g,"\\'")+'?\';window.sendMsg&&sendMsg();}},100)">Ask VoterLens about '+stateName+' \u2192</button></div>'+
        '</div>'+
      '</div>';
    panel.scrollIntoView({behavior:'smooth',block:'nearest'});
    try{if(typeof earnBadge==='function')earnBadge('state');}catch(e){}
  };
    if(document.getElementById('chat-state')) document.getElementById('chat-state').value=abbr;
    if(typeof goPage==='function') goPage('chat');
    setTimeout(function(){var ta=document.getElementById('chat-ta'); if(ta){ta.value='Help me find official polling-place and election-office mailing-location resources for '+s.n+(z.trim()?(' near '+z.trim()):'')+'. Use only Vote.gov, USA.gov, EAC.gov, and official state/local election websites.'; if(typeof sendMsg==='function') sendMsg();}},160);
  };
  function bindMapClicks(){
    document.addEventListener('click',function(e){
      var state=e.target.closest && e.target.closest('.bb-state');
      if(state){var m=(state.getAttribute('class')||'').match(/bb-state-([A-Z]{2})/); if(m){e.preventDefault();e.stopPropagation();if(e.stopImmediatePropagation)e.stopImmediatePropagation();window.showStateLocator(m[1]);return false;}}
    },true);
    var cards=document.getElementById('state-cards');
    if(cards){cards.querySelectorAll('.state-card').forEach(function(card){var nm=(card.querySelector('.sc-name')||{}).textContent;var found=(window.STATES||[]).find(function(s){return s.n===nm});if(found){card.onclick=function(ev){ev.preventDefault();window.showStateLocator(found.a);};}});}
  }
  ready(function(){setHeroPeriods();bindMapClicks(); if(document.getElementById('state-locator-panel')&&!document.querySelector('#state-locator-panel .locator-empty')) closeStateLocator();});
})();
</script>


<script>
/* FINAL PATCH JS — no badges, accurate world globe using Natural Earth / world-atlas, better state expansion defaults */
(function(){
  // Remove badges links/pages in case older markup reappears.
  function removeBadges(){
    ['nb-badges','md-badges','pg-badges'].forEach(function(id){var el=document.getElementById(id); if(el) el.remove();});
  }
  removeBadges();
  document.addEventListener('DOMContentLoaded', removeBadges);

  function loadScriptOnce(src){
    return new Promise(function(resolve,reject){
      var found=[].slice.call(document.scripts).find(function(s){return s.src===src;});
      if(found){resolve();return;}
      var s=document.createElement('script'); s.src=src; s.onload=resolve; s.onerror=reject; document.head.appendChild(s);
    });
  }
  function ensureD3Topo(){
    var p=Promise.resolve();
    if(!window.d3) p=p.then(function(){return loadScriptOnce('https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js');});
    if(!window.topojson) p=p.then(function(){return loadScriptOnce('https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js');});
    return p;
  }

  window.initHeroGlobe = function(){
    var canvas=document.getElementById('globe-c');
    if(!canvas || canvas._accurateGlobe) return;
    canvas._accurateGlobe=true;
    var wrap=canvas.parentElement;
    if(!wrap) return;
    // Keep the original canvas globe visible until the accurate D3 globe is fully loaded.
    // This prevents the hero globe from disappearing when the page is opened locally or CDN is slow.
    canvas.style.display='block';
    wrap.style.pointerEvents='auto';
    var tip=document.createElement('div');
    tip.className='globe-tooltip';
    tip.textContent='Drag the globe — United States highlighted';
    wrap.appendChild(tip);
    ensureD3Topo().then(function(){
      return Promise.all([
        fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/land-110m.json').then(function(r){return r.json();}),
        fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json').then(function(r){return r.json();})
      ]);
    }).then(function(res){
      var land=topojson.feature(res[0],res[0].objects.land);
      var countries=topojson.feature(res[1],res[1].objects.countries).features;
      var usa=countries.filter(function(f){return String(f.id)==='840';})[0];
      // Accurate globe is ready: now swap from canvas to the interactive SVG.
      canvas.style.display='none';
      wrap.querySelectorAll('.bb-orthographic-globe').forEach(function(n){n.remove();});
      var svg=d3.select(wrap).append('svg').attr('class','bb-orthographic-globe').attr('aria-label','Interactive globe with the United States highlighted');
      var g=svg.append('g');
      var defs=svg.append('defs');
      var oceanGrad=defs.append('radialGradient').attr('id','bbOceanGrad').attr('cx','35%').attr('cy','28%').attr('r','72%');
      oceanGrad.append('stop').attr('offset','0%').attr('stop-color','#5ea8ff');
      oceanGrad.append('stop').attr('offset','45%').attr('stop-color','#103c74');
      oceanGrad.append('stop').attr('offset','100%').attr('stop-color','#031128');
      var glow=defs.append('filter').attr('id','bbGlow').attr('x','-80%').attr('y','-80%').attr('width','260%').attr('height','260%');
      glow.append('feGaussianBlur').attr('stdDeviation','5').attr('result','b');
      var m=glow.append('feMerge'); m.append('feMergeNode').attr('in','b'); m.append('feMergeNode').attr('in','SourceGraphic');
      var projection=d3.geoOrthographic().rotate([96,-35]).precision(.45);
      var path=d3.geoPath(projection);
      var dragStart=null, rotStart=null, paused=false;
      function themeLight(){return document.documentElement.getAttribute('data-theme')==='light';}
      function size(){
        var W=wrap.clientWidth||560,H=wrap.clientHeight||560,R=Math.min(W,H)*.48;
        svg.attr('viewBox','0 0 '+W+' '+H).attr('width',W).attr('height',H);
        projection.translate([W/2,H/2]).scale(R);
        draw();
      }
      function draw(){
        var W=wrap.clientWidth||560,H=wrap.clientHeight||560,R=Math.min(W,H)*.48,cx=W/2,cy=H/2;
        g.selectAll('*').remove();
        g.append('circle').attr('cx',cx).attr('cy',cy).attr('r',R).attr('fill','url(#bbOceanGrad)').attr('stroke',themeLight()?'rgba(29,78,216,.42)':'rgba(147,197,253,.55)').attr('stroke-width',1.2);
        g.append('path').datum(d3.geoGraticule10()).attr('d',path).attr('fill','none').attr('stroke',themeLight()?'rgba(30,64,175,.16)':'rgba(147,197,253,.14)').attr('stroke-width',.55);
        g.append('path').datum(land).attr('d',path).attr('fill',themeLight()?'#f8fafc':'#19345e').attr('stroke',themeLight()?'rgba(30,64,175,.24)':'rgba(147,197,253,.18)').attr('stroke-width',.45);
        if(usa){
          g.append('path').datum(usa).attr('d',path).attr('class','bb-us-glow').attr('fill',themeLight()?'#f59e0b':'#fbbf24').attr('fill-opacity',themeLight()?.86:.9).attr('stroke','#fff7c2').attr('stroke-width',1.8).attr('filter','url(#bbGlow)');
          g.append('path').datum(usa).attr('d',path).attr('fill','none').attr('stroke',themeLight()?'#b91c1c':'#fde68a').attr('stroke-width',.85);
        }
        g.append('circle').attr('cx',cx).attr('cy',cy).attr('r',R).attr('fill','none').attr('stroke',themeLight()?'rgba(96,165,250,.45)':'rgba(147,197,253,.70)').attr('stroke-width',2.2);
        g.append('circle').attr('cx',cx-R*.22).attr('cy',cy-R*.28).attr('r',R*.70).attr('fill','rgba(255,255,255,'+(themeLight()?'.16':'.07')+')').attr('opacity','.65');
      }
      svg.on('pointerenter',function(){tip.classList.add('show'); paused=true;})
         .on('pointerleave',function(){tip.classList.remove('show'); paused=false; dragStart=null;})
         .on('pointerdown',function(event){paused=true; dragStart=[event.clientX,event.clientY]; rotStart=projection.rotate(); svg.node().setPointerCapture&&svg.node().setPointerCapture(event.pointerId);})
         .on('pointermove',function(event){ if(!dragStart) return; var dx=event.clientX-dragStart[0], dy=event.clientY-dragStart[1]; projection.rotate([rotStart[0]+dx*.35, Math.max(-70,Math.min(70,rotStart[1]-dy*.22)), rotStart[2]]); draw(); })
         .on('pointerup',function(event){dragStart=null; svg.node().releasePointerCapture&&svg.node().releasePointerCapture(event.pointerId);});
      var ro=new ResizeObserver(size); ro.observe(wrap); size();
      d3.timer(function(){ if(!paused && !dragStart){ var r=projection.rotate(); projection.rotate([r[0]+.018,r[1],r[2]]); draw(); }});
      new MutationObserver(draw).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
    }).catch(function(){
      // Fall back to the original canvas globe if CDN is unavailable.
      canvas.style.display='block';
      wrap.querySelectorAll('.bb-orthographic-globe').forEach(function(n){n.remove();});
      if(tip) tip.textContent='Interactive globe — drag to explore';
    });
  };

  function restoreHeroGlobeNow(){
    try { window.initHeroGlobe && window.initHeroGlobe(); } catch(e) {}
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', restoreHeroGlobeNow);
  else restoreHeroGlobeNow();
  setTimeout(restoreHeroGlobeNow, 600);
  setTimeout(restoreHeroGlobeNow, 1800);

  // Make the question cards flow neatly even if generated late.
  function polishQuestionCards(){
    var grid=document.getElementById('cards-grid');
    if(!grid) return;
    grid.querySelectorAll('.q-card').forEach(function(card){card.classList.add('visible');});
  }
  document.addEventListener('DOMContentLoaded',polishQuestionCards);
  setTimeout(polishQuestionCards,800);
})();
</script>


<style>
/* HOTFIX — restored globe visibility and cleaner light-mode rendering */
.globe-wrap{min-width:360px;min-height:360px;}
.globe-wrap canvas#globe-c{display:block;position:absolute;inset:0;width:100%!important;height:100%!important;z-index:1;}
.globe-wrap .bb-orthographic-globe{position:absolute;inset:0;z-index:2;width:100%!important;height:100%!important;display:block!important;}
[data-theme="light"] .globe-wrap{filter:drop-shadow(0 28px 52px rgba(30,64,120,.22));}
[data-theme="light"] .bb-orthographic-globe{filter:drop-shadow(0 22px 44px rgba(30,64,175,.22)) saturate(1.04);}
</style>



<!-- HOTFIX: restore Voting Rights Help + Voting Plan dropdown/actions -->
<style id="vl-interaction-hotfix-css">
  .emer-fab{pointer-events:auto!important;z-index:9999!important;outline:none!important;user-select:none!important;}
  .emer-fab:focus{box-shadow:0 0 0 3px rgba(96,165,250,.45),0 0 26px var(--red-glow)!important;}
  .modal-backdrop{z-index:10000!important;}
  .modal-backdrop.open{display:flex!important;}
  #pg-plan .plan-step{overflow:visible!important;}
  #plan-state,.state-sel{position:relative!important;z-index:20!important;pointer-events:auto!important;appearance:auto!important;-webkit-appearance:menulist!important;}
  #pg-plan .ps-opt,#pg-plan .plan-generate-btn{position:relative!important;z-index:20!important;pointer-events:auto!important;}
  #pg-plan .plan-step::after{pointer-events:none!important;z-index:0!important;}
  [data-theme="light"] #plan-state{background:#ffffff!important;color:#0b1224!important;border-color:rgba(15,23,42,.18)!important;}
  [data-theme="dark"] #plan-state{background:rgba(255,255,255,.06)!important;color:#f5f0e8!important;}
  #plan-state option{color:#0b1224!important;background:#ffffff!important;}

/* Locator fact rows — state-specific info display */
.locator-facts{display:flex;flex-direction:column;gap:8px;margin:12px 0}
.lf-row{display:flex;gap:8px;align-items:flex-start;font-size:12.5px;line-height:1.5}
.lf-label{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--text3);min-width:130px;padding-top:1px;flex-shrink:0}
.lf-val{color:var(--text);font-weight:500}
</style>
<script id="vl-interaction-hotfix-js">
(function(){
  function byId(id){return document.getElementById(id);}
  function getStates(){
    if(Array.isArray(window.STATES) && window.STATES.length) return window.STATES;
    return [
      ['AL','Alabama'],['AK','Alaska'],['AZ','Arizona'],['AR','Arkansas'],['CA','California'],['CO','Colorado'],['CT','Connecticut'],['DE','Delaware'],['FL','Florida'],['GA','Georgia'],['HI','Hawaii'],['ID','Idaho'],['IL','Illinois'],['IN','Indiana'],['IA','Iowa'],['KS','Kansas'],['KY','Kentucky'],['LA','Louisiana'],['ME','Maine'],['MD','Maryland'],['MA','Massachusetts'],['MI','Michigan'],['MN','Minnesota'],['MS','Mississippi'],['MO','Missouri'],['MT','Montana'],['NE','Nebraska'],['NV','Nevada'],['NH','New Hampshire'],['NJ','New Jersey'],['NM','New Mexico'],['NY','New York'],['NC','North Carolina'],['ND','North Dakota'],['OH','Ohio'],['OK','Oklahoma'],['OR','Oregon'],['PA','Pennsylvania'],['RI','Rhode Island'],['SC','South Carolina'],['SD','South Dakota'],['TN','Tennessee'],['TX','Texas'],['UT','Utah'],['VT','Vermont'],['VA','Virginia'],['WA','Washington'],['WV','West Virginia'],['WI','Wisconsin'],['WY','Wyoming'],['DC','District of Columbia']
    ].map(function(x){return {a:x[0],n:x[1]};});
  }
  function populatePlanState(){
    var el=byId('plan-state'); if(!el) return;
    var cur=el.value || (byId('home-state')&&byId('home-state').value) || (byId('chat-state')&&byId('chat-state').value) || 'GA';
    var states=getStates();
    el.innerHTML=states.map(function(s){return '<option value="'+s.a+'">'+s.n+'</option>';}).join('');
    el.value=states.some(function(s){return s.a===cur;})?cur:'GA';
    el.disabled=false;
  }
  window.openEmer=function(){
    var m=byId('emer-modal');
    if(m){m.classList.add('open');m.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';}
  };
  window.closeEmer=function(){
    var m=byId('emer-modal');
    if(m){m.classList.remove('open');m.setAttribute('aria-hidden','true');document.body.style.overflow='';}
  };
  window.closeEmerOutside=function(e){
    if(e && e.target && e.target.id==='emer-modal') window.closeEmer();
  };
  window.emerAsk=function(q){
    window.closeEmer();
    if(typeof goPage==='function') goPage('chat');
    setTimeout(function(){
      var ta=byId('chat-ta');
      if(ta){ta.value=q; if(typeof sendMsg==='function') sendMsg();}
    },180);
  };
  window.selOpt=function(btn){
    if(!btn) return;
    var group=btn.getAttribute('data-group');
    document.querySelectorAll('.ps-opt[data-group="'+group+'"]').forEach(function(b){b.classList.remove('sel');b.setAttribute('aria-pressed','false');});
    btn.classList.add('sel');btn.setAttribute('aria-pressed','true');
  };
  window.selOptMulti=function(btn){
    if(!btn) return;
    var group=btn.getAttribute('data-group');
    var val=btn.getAttribute('data-val');
    if(val==='none'){
      document.querySelectorAll('.ps-opt[data-group="'+group+'"]').forEach(function(b){b.classList.remove('sel');b.setAttribute('aria-pressed','false');});
      btn.classList.add('sel');btn.setAttribute('aria-pressed','true');
      return;
    }
    var none=document.querySelector('.ps-opt[data-group="'+group+'"][data-val="none"]');
    if(none){none.classList.remove('sel');none.setAttribute('aria-pressed','false');}
    btn.classList.toggle('sel');btn.setAttribute('aria-pressed',btn.classList.contains('sel')?'true':'false');
  };
  function bindClicks(){
    var fab=document.querySelector('.emer-fab');
    if(fab){fab.onclick=function(e){e.preventDefault();e.stopPropagation();window.openEmer();};}
    var close=document.querySelector('#emer-modal .modal-close');
    if(close){close.onclick=function(e){e.preventDefault();window.closeEmer();};}
    var modal=byId('emer-modal');
    if(modal){modal.onclick=function(e){window.closeEmerOutside(e);};}
    document.querySelectorAll('.emer-q-btn').forEach(function(b){
      if(!b.dataset.boundEmergency){b.dataset.boundEmergency='1'; b.addEventListener('click',function(e){e.stopPropagation();});}
    });
  }
  function ready(){populatePlanState();bindClicks();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',ready); else ready();
  window.addEventListener('load',function(){setTimeout(ready,50);setTimeout(ready,500);});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')window.closeEmer();});
  var oldGo=window.goPage;
  if(typeof oldGo==='function' && !oldGo._bbPlanPatch){
    window.goPage=function(p){var r=oldGo.apply(this,arguments); if(p==='plan')setTimeout(populatePlanState,80); return r;};
    window.goPage._bbPlanPatch=true;
  }
})();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/healthz")
def healthz():
    return "ok", 200

@app.route("/api/chat", methods=["POST"])
def api_chat():
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "Server is missing the ANTHROPIC_API_KEY environment variable."}), 500

    data = request.get_json(silent=True) or {}
    system = data.get("system", "")
    messages = data.get("messages", [])
    try:
        max_tokens = int(data.get("max_tokens", 1200))
    except (TypeError, ValueError):
        max_tokens = 1200
    max_tokens = max(1, min(max_tokens, 2000))

    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "messages is required and must be a non-empty list."}), 400

    try:
        upstream = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "content-type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "system": system,
                "messages": messages,
            },
            timeout=60,
        )
    except requests.RequestException as e:
        return jsonify({"error": f"Upstream request to Anthropic failed: {e}"}), 502

    return (upstream.content, upstream.status_code, {"Content-Type": "application/json"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
