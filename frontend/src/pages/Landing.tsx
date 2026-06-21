import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Landing.css';

export const Landing: React.FC = () => {
  useEffect(() => {
    const reveals = document.querySelectorAll('.reveal');
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in'); });
    }, { threshold: 0.15 });
    reveals.forEach(el => io.observe(el));

    const cards = document.querySelectorAll<HTMLElement>('.card');
    cards.forEach(card => {
      card.addEventListener('mousemove', (e: any) => {
        const c = card as HTMLElement;
        const r = c.getBoundingClientRect();
        c.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        c.style.setProperty('--my', (e.clientY - r.top) + 'px');
      });
    });
  }, []);

  return (
    <div className="landing-root">
      <div className="grid-bg"></div>
      <div className="glow glow-1"></div>
      <div className="glow glow-2"></div>
      <div className="glow glow-3"></div>

      <nav className="landing-nav">
        <Link to="/" className="brand">
          <span className="dot"></span> GRIDLOCK
        </Link>
        <div className="nav-links">
          <a href="#problem">Problem</a>
          <a href="#solution">Solution</a>
          <a href="#pipeline">Pipeline</a>
          <a href="#team">Team</a>
        </div>
        <Link to="/app/live" className="nav-cta">Launch Dashboard</Link>
      </nav>

      <section className="hero">
        <div className="hero-tag">Flipkart GridLock · Round 2 Submission</div>
        <h1>GRIDLOCK</h1>
        <h2>Predictive intelligence for Bengaluru's traffic incidents</h2>
        <p className="lede">
          Every disruptive event on the road — a breakdown, a flood, a protest — is a question the city can't
          answer fast enough: how bad will it get, what should we deploy, and did it actually work? GridLock turns
          8,173 historical events into a real-time advisory engine that answers all three.
        </p>
        <div className="hero-ctas">
          <Link to="/app/live" className="btn btn-primary">Launch Live Dashboard →</Link>
          <a href="#pipeline" className="btn btn-ghost">See How It Works</a>
        </div>
        <div className="scroll-cue"><i></i></div>
      </section>

      <section id="problem">
        <div className="section-head reveal">
          <div className="kicker">The Problem</div>
          <h3>Bengaluru's roads break in the same ways, over and over</h3>
          <p>Traffic police respond to thousands of disruptive events with no quantitative system —
              just instinct, radio calls, and whoever's closest.</p>
        </div>

        <div className="problem-grid">
          <div className="photo-stack reveal">
            <img className="p1" src="/images/_92729063_newairportroadnearhebbal.webp" alt="congested city traffic" />
            <img className="p2" src="/images/bangalore-city-scape.webp" alt="rainy flooded street" />
            <img className="p3" src="/images/unverified-content-long-exposure-of-traffic-at-night-in-downtown-bangalore-india.webp" alt="city traffic at night" />
          </div>

          <div className="problem-list reveal">
            <div className="problem-item">
              <div className="num">01</div>
              <div>
                <h4>How bad will this get?</h4>
                <p>No way to estimate duration, road closure odds, or how far congestion will spread before it's
                    already a citywide jam.</p>
              </div>
            </div>
            <div className="problem-item">
              <div className="num">02</div>
              <div>
                <h4>What should we deploy?</h4>
                <p>Officer counts, barricades, and diversions are decided on the spot, with no historical
                    evidence to back the call.</p>
              </div>
            </div>
            <div className="problem-item">
              <div className="num">03</div>
              <div>
                <h4>Did it work? Are we learning?</h4>
                <p>Every event is treated as brand new — outcomes vanish into a logbook nobody re-reads, and the
                    same mistakes repeat.</p>
              </div>
            </div>
            <div className="problem-item">
              <div className="num">04</div>
              <div>
                <h4>One event, isolated</h4>
                <p>An incident isn't just a pin on a map. It has network position, blast radius, and neighbors
                    competing for the same officers — and today none of that context is used.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="solution">
        <div className="section-head reveal">
          <div className="kicker">The Solution</div>
          <h3>One advisory engine, built on honest models</h3>
          <p>Every event is reconstructed with its full context — then scored, ranked, and matched against history,
              with every model reporting its own confidence instead of hiding it.</p>
        </div>

        <div className="cards reveal">
          {[
            { icon: '⚡', title: 'Triage Classifier', text: 'Calibrated closure probability and priority — isotonic-calibrated so "12%" is an honest, empirically-real number, not a raw tree score.' },
            { icon: '⏱', title: 'Three-Track Duration', text: 'Fast (quantile regression), Slow (survival analysis for censored "still active" events), and Escalation (flagged for civic handoff) — because one model can\'t fit three different distributions.' },
            { icon: '🌐', title: 'Spread & Cascade Risk', text: 'Congestion footprint computed via real road-network Dijkstra propagation, not as-the-crow-flies radius.' },
            { icon: '🚧', title: 'Resource Recommender', text: 'Officer counts, simulated barricade placement, and named diversion routes with real travel-time deltas.' },
            { icon: '🔎', title: 'Case-Based Retrieval', text: 'Surfaces the 3-5 most similar past events and what actually happened — making every recommendation auditable by a human.' },
            { icon: '⚠️', title: 'Network Resilience', text: 'Checks if alternate routes are already compromised by nearby events — warning that the last bypass is about to absorb the overflow, before it happens.' },
          ].map((item, i) => (
            <div key={i} className="card">
              <div className="card-num">{String(i + 1).padStart(2, '0')}</div>
              <div className="icon">{item.icon}</div>
              <h4>{item.title}</h4>
              <p>{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="pipeline">
        <div className="section-head reveal">
          <div className="kicker">Core Architecture</div>
          <h3>Ten stages, one advisory</h3>
          <p>Raw event log in, structured advisory out — every stage persists what it learns so a single new
              event can be scored in real time using only cached artifacts.</p>
        </div>

        <div className="pipeline-visual reveal">
          <div className="ring-wrap">
            <svg className="ring-svg" viewBox="0 0 100 100">
              <circle className="ring-circle" cx="50" cy="50" r="46"></circle>
            </svg>
            <div className="ring-orbit">
              <div className="ring-pointer"></div>
            </div>
            <div className="ring-orbit rev">
              <div className="ring-pointer"></div>
            </div>
            <div className="ring-hub"><b>10</b><span>stages · circular pipeline</span></div>

            {[
              { s: '01', t: 'Data Cleaning', d: 'Timestamp fixes, cause normalization, track assignment.', style: { left: '50%', top: '10%' } },
              { s: '02', t: 'Spatial Enrichment', d: 'Zone KNN-fill, OSM road-graph snap, centrality.', style: { left: '73.51%', top: '17.64%' } },
              { s: '03', t: 'External Signals', d: 'Rainfall, holidays, IPL, election windows.', style: { left: '88.04%', top: '37.64%' } },
              { s: '04', t: 'Feature Engineering', d: 'Cyclical encoding, out-of-fold target encoding.', style: { left: '88.04%', top: '62.36%' } },
              { s: '05', t: 'Triage Classifier', d: 'CatBoost + manual OOF + isotonic calibration.', style: { left: '73.51%', top: '82.36%' } },
              { s: '06', t: 'Duration Models', d: 'XGBoost quantiles / Weibull AFT / BBMP handoff.', style: { left: '50%', top: '90%' } },
              { s: '07', t: 'Spread Model', d: 'Dijkstra + exponential decay footprint, O(n).', style: { left: '26.49%', top: '82.36%' } },
              { s: '08', t: 'Resource Recommender', d: 'Officers, barricade simulation, diversion routing.', style: { left: '11.96%', top: '62.36%' } },
              { s: '09', t: 'Case-Based Retrieval', d: 'Cosine nearest neighbors over 37 features.', style: { left: '11.96%', top: '37.64%' } },
              { s: '10', t: 'Advisory Engine', d: 'Ties every stage into one auditable output.', style: { left: '26.49%', top: '17.64%' } },
            ].map((node, i) => (
              <div key={i} className="ring-node" style={node.style}>
                <div className="s-num">STAGE {node.s}</div>
                <h5>{node.t}</h5>
                <p>{node.d}</p>
              </div>
            ))}
          </div>
          <p className="ring-hint">Hover a stage · the loop closes back to Stage 01, same as every event replays through the full pipeline</p>

          <div className="pipeline-fallback">
             {[
              { s: '01', t: 'Data Cleaning', d: 'Timestamp fixes, cause normalization, track assignment.' },
              { s: '02', t: 'Spatial Enrichment', d: 'Zone KNN-fill, OSM road-graph snap, centrality.' },
              { s: '03', t: 'External Signals', d: 'Rainfall, holidays, IPL, election windows.' },
              { s: '04', t: 'Feature Engineering', d: 'Cyclical encoding, out-of-fold target encoding.' },
              { s: '05', t: 'Triage Classifier', d: 'CatBoost + manual OOF + isotonic calibration.' },
              { s: '06', t: 'Duration Models', d: 'XGBoost quantiles / Weibull AFT / BBMP handoff.' },
              { s: '07', t: 'Spread Model', d: 'Dijkstra + exponential decay footprint, O(n).' },
              { s: '08', t: 'Resource Recommender', d: 'Officers, barricade simulation, diversion routing.' },
              { s: '09', t: 'Case-Based Retrieval', d: 'Cosine nearest neighbors over 37 features.' },
              { s: '10', t: 'Advisory Engine', d: 'Ties every stage into one auditable output.' },
            ].map((node, i) => (
              <div key={i} className="fb-node">
                <div className="fb-dot">{node.s}</div>
                <div className="fb-text">
                  <h5>{node.t}</h5>
                  <p>{node.d}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="arch-diagram reveal">
          <div className="arch-box">
            <div className="tk">Input</div>
            <h5>Single Event</h5>
            <p>Cause, zone, lat/lon, timestamp — featurized from scratch using only cached artifacts.</p>
          </div>
          <div className="arch-box">
            <div className="tk">Core</div>
            <h5>Calibrated Models</h5>
            <p>Triage + duration + spread + retrieval, each scoped to what the data actually supports.</p>
          </div>
          <div className="arch-box">
            <div className="tk">Output</div>
            <h5>Structured Advisory</h5>
            <p>Closure %, duration band, officer count, diversions, resilience warning, similar cases.</p>
          </div>
        </div>
      </section>

      <section id="team">
        <div className="section-head reveal">
          <div className="kicker">Our Information</div>
          <h3>The team behind GridLock</h3>
          <p>Professional predictive intelligence for Bengaluru traffic incidents.</p>
        </div>

        <div className="team-grid reveal">
          {[
            { name: 'Sneh Kansagara', role: 'AI/ML Engineer (Team Leader)', pos: 'center', scale: 1 },
            { name: 'Akshat Tripathi', role: 'ML & Backend Engineer', pos: 'center', scale: 1 },
            { name: 'Advait Mishra', role: 'Frontend & Backend Engineer', pos: 'center', scale: 1 },
            { name: 'Priyanshu Jha', role: 'Cloud & MLOps Engineer', pos: '100% 0%', scale: 1.6 },
          ].map((member, i) => (
            <div key={i} className="team-card">
              <div className="team-photo">
                <img
                  src={`/team/${i + 1}.jpeg`}
                  alt={member.role}
                  style={{ objectPosition: member.pos, transform: `scale(${member.scale})` }}
                />
              </div>
              <div className="team-info">
                <h4>{member.name}</h4>
                <span className="role">{member.role}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <footer>
        <div className="brand"><span className="dot"></span> GRIDLOCK</div>
        <p>Flipkart GridLock Round 2 — Predictive intelligence for Bengaluru traffic incidents.</p>
        <div className="links">
          <a href="#problem">Problem</a>
          <a href="#solution">Solution</a>
          <a href="#pipeline">Pipeline</a>
          <a href="#team">Team</a>
        </div>
        <div className="footer-contact">
          <a href="tel:+917990409021">+91 79904 09021</a>
          <span className="sep">·</span>
          <a href="mailto:snehkansagara@gmail.com">snehkansagara@gmail.com</a>
        </div>
      </footer>
    </div>
  );
};
