/* Shared prep-collection navigation — the ONE place this list lives.
 *
 * Add a document: add one entry to LINKS below. Every page picks it up on reload.
 * Do NOT paste a <nav class="sitenav"> back into a page; that is what this replaced
 * (the list had drifted into 7 different versions across 65 files).
 *
 * Each page carries:  <div id="sitenav"></div><script src="sitenav.js"></script>
 * The CSS still lives in each page's own <style> block (nav.sitenav rules).
 *
 * Generated 2026-09-21; edit this file directly from here on.
 */
(function () {
  var LINKS = [
      {
          "h": "papercusp-answer-bank",
          "t": "Answer&nbsp;Bank"
      },
      {
          "h": "citi-senior-ai-engineer",
          "t": "Citi&nbsp;·&nbsp;Senior&nbsp;AI"
      },
      {
          "h": "restart-scout-chatbot-infrastructure",
          "t": "Restart&nbsp;Chatbot&nbsp;Infra"
      },
      {
          "h": "braid-guido-cossu-founder-call",
          "t": "Braid&nbsp;·&nbsp;Guido&nbsp;Cossu"
      },
      {
          "h": "jpmc-payments-ai-developer-portal",
          "t": "Chase&nbsp;·&nbsp;Steven&nbsp;·&nbsp;Coding&nbsp;4&nbsp;pm"
      },
      {
          "h": "interview-feedback-answers",
          "t": "Feedback&nbsp;Answers"
      },
      {
          "h": "vantor-agentic-engineering-lead",
          "t": "Vantor&nbsp;Agentic&nbsp;Lead"
      },
      {
          "h": "servicenow-staff-ml-interview-prep",
          "t": "ServiceNow&nbsp;Staff&nbsp;ML"
      },
      {
          "h": "acadian-senior-ai-engineer",
          "t": "Acadian&nbsp;Senior&nbsp;AI"
      },
      {
          "h": "cider-forward-deployed-engineer",
          "t": "Cider&nbsp;FDE"
      },
      {
          "h": "eliseai-senior-security-engineer",
          "t": "EliseAI&nbsp;Security"
      },
      {
          "h": "steampunk-senior-ai-developer",
          "t": "Steampunk&nbsp;AI&nbsp;Developer"
      },
      {
          "h": "twg-recruiter-screen",
          "t": "TWG&nbsp;Global"
      },
      {
          "h": "scowtt-data-platform-screen",
          "t": "Scowtt&nbsp;Data&nbsp;Platform"
      },
      {
          "h": "rtx-hirevue-prep",
          "t": "RTX&nbsp;Screen"
      },
      {
          "h": "hyundai-autoever-applied-ai-hm-call",
          "t": "Hyundai&nbsp;AutoEver"
      },
      {
          "h": "kaseya-codesignal-mle-core",
          "t": "Kaseya&nbsp;CodeSignal"
      },
      {
          "h": "experian-sova-assessment",
          "t": "Experian&nbsp;Sova"
      },
      {
          "h": "roblox-assessments",
          "t": "Roblox&nbsp;Games"
      },
      {
          "h": "arrivia-member-travel-concierge",
          "t": "arrivia&nbsp;System&nbsp;Design"
      },
      {
          "h": "arrivia-evp-shawn-sandy",
          "t": "arrivia&nbsp;EVP&nbsp;Call"
      },
      {
          "h": "emergent-ai-director-testgorilla",
          "t": "Emergent&nbsp;AI&nbsp;Director"
      },
      {
          "h": "creatoriq-agentic-experience-prep",
          "t": "CreatorIQ&nbsp;Agentic"
      },
      {
          "h": "flosum-ai-gtm",
          "t": "Flosum&nbsp;AI&nbsp;GTM"
      },
      {
          "h": "rackspace-fde",
          "t": "Rackspace&nbsp;FDE"
      },
      {
          "h": "m3-senior-agentic-engineer",
          "t": "M3&nbsp;Agentic"
      },
      {
          "h": "anthropic-technical-advisor",
          "t": "Anthropic&nbsp;Advisor"
      },
      {
          "h": "anthropic-codesignal-assessment",
          "t": "Anthropic&nbsp;CodeSignal"
      },
      {
          "h": "capital-one-codesignal-assessment",
          "t": "Capital&nbsp;One&nbsp;GCA"
      },
      {
          "h": "citi-karat-python-interview",
          "t": "Citi&nbsp;Karat"
      },
      {
          "h": "thomson-reuters-cocounsel-lead",
          "t": "TR&nbsp;CoCounsel"
      },
      {
          "h": "verizon-ai-control-plane-screen",
          "t": "Verizon&nbsp;Control&nbsp;Plane"
      },
      {
          "h": "turing-ai-eval-coding-agents",
          "t": "Turing&nbsp;AI&nbsp;Eval"
      },
      {
          "h": "micro1-forward-deployed-engineer",
          "t": "micro1&nbsp;FDE"
      },
      {
          "h": "micro1-electron-engineer",
          "t": "micro1&nbsp;Electron"
      },
      {
          "h": "micro1-internal-platforms",
          "t": "micro1&nbsp;Platforms"
      },
      {
          "h": "micro1-senior-engineer",
          "t": "micro1&nbsp;Senior&nbsp;SWE"
      },
      {
          "h": "micro1-fullstack-engineer",
          "t": "micro1&nbsp;Fullstack"
      },
      {
          "h": "micro1-aiml-engineer",
          "t": "micro1&nbsp;AI/ML"
      },
      {
          "h": "micro1-data-platforms",
          "t": "micro1&nbsp;Data&nbsp;Platforms"
      },
      {
          "h": "mercor-deeptune-mts-prep",
          "t": "Mercor&nbsp;Deeptune"
      },
      {
          "h": "lilly-agentic-reliability-platform",
          "t": "Lilly&nbsp;Agentic&nbsp;Platform"
      },
      {
          "h": "boom-supersonic-full-stack",
          "t": "Boom&nbsp;Supersonic"
      },
      {
          "h": "mcp-cicd-study-faq",
          "t": "CI/CD&nbsp;+&nbsp;MCP&nbsp;FAQ"
      },
      {
          "h": "python-gotchas",
          "t": "Python&nbsp;Gotchas"
      }
  ];

  // Right-aligned reference group starts here.
  var SEP_BEFORE = "mcp-cicd-study-faq";

  var file = (location.pathname.split('/').pop() || '').replace(/[?#].*$/, '');
  var standalone = /-standalone\.html$/.test(file);
  var slug = file.replace(/-standalone\.html$/, '').replace(/\.html$/, '');

  var nav = document.createElement('nav');
  nav.className = 'sitenav';
  nav.setAttribute('aria-label', 'Prep documents');
  var activeLink = null;

  LINKS.forEach(function (link) {
    if (link.h === SEP_BEFORE) {
      var sep = document.createElement('span');
      sep.className = 'sep';
      nav.appendChild(sep);
    }
    var a = document.createElement('a');
    a.setAttribute('href', link.h + (standalone ? '-standalone' : '') + '.html');
    a.innerHTML = link.t;
    if (link.h === slug) {
      a.setAttribute('aria-current', 'page');
      activeLink = a;
    }
    nav.appendChild(a);
  });

  function revealActive() {
    if (!activeLink || nav.scrollWidth <= nav.clientWidth) return;
    var viewport = nav.getBoundingClientRect();
    var target = activeLink.getBoundingClientRect();
    nav.scrollLeft += target.left - viewport.left - (viewport.width - target.width) / 2;
  }

  var mount = document.getElementById('sitenav');
  if (mount && mount.parentNode) {
    mount.parentNode.replaceChild(nav, mount);
    revealActive();
  }
  else document.addEventListener('DOMContentLoaded', function () {
    var late = document.getElementById('sitenav');
    if (late && late.parentNode) {
      late.parentNode.replaceChild(nav, late);
      revealActive();
    }
  });
  window.addEventListener('resize', revealActive);
})();
