
(function(){
  window.dataLayer = window.dataLayer || [];
  var fired = {};
  function pushEvent(name, props){
    try {
      var payload = Object.assign({event: name, page_path: location.pathname}, props || {});
      window.dataLayer.push(payload);
      if (typeof window.gtag === 'function') {
        var gaProps = Object.assign({}, props || {});
        if (gaProps.page_path == null) gaProps.page_path = location.pathname;
        window.gtag('event', name, gaProps);
      }
      if (window.console && console.debug) console.debug('[Lakefront analytics]', payload);
      try {
        var items = JSON.parse(sessionStorage.getItem('lakefront_events') || '[]');
        items.push(Object.assign({ts: Date.now()}, payload));
        sessionStorage.setItem('lakefront_events', JSON.stringify(items.slice(-100)));
      } catch (e) {}
    } catch (e) {}
  }

  function preserveUTM() {
    var params = new URLSearchParams(location.search);
    var keep = ['utm_source','utm_medium','utm_campaign','utm_term','utm_content','gclid','fbclid','ttclid','msclkid'];
    var found = keep.filter(function(k){ return params.has(k); });
    if (!found.length) return;
    var links = document.querySelectorAll('a[href]');
    links.forEach(function(link){
      try {
        var href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('tel:') || href.startsWith('mailto:') || href.startsWith('javascript:')) return;
        var url = new URL(href, location.origin);
        if (url.origin !== location.origin) return;
        keep.forEach(function(k){ if (params.has(k) && !url.searchParams.has(k)) url.searchParams.set(k, params.get(k)); });
        link.setAttribute('href', url.pathname + url.search + url.hash);
      } catch (e) {}
    });
  }

  function trackClicks() {
    document.addEventListener('click', function(e){
      var a = e.target.closest('a, button');
      if (!a) return;
      var text = (a.innerText || a.textContent || '').trim().replace(/\s+/g,' ').slice(0,80);
      if (a.matches('a[href^="tel:"]')) {
        pushEvent('phone_click', {link_text: text, phone_number: a.getAttribute('href').replace('tel:','')});
        return;
      }
      if (a.matches('a[href^="mailto:"]')) {
        pushEvent('email_click', {link_text: text, email: a.getAttribute('href').replace('mailto:','')});
        return;
      }
      if (a.classList.contains('button') || a.classList.contains('stickybtn') || /call|quote|schedule|contact/i.test(text)) {
        pushEvent('cta_click', {link_text: text, destination: a.getAttribute('href') || ''});
      }
    }, true);
  }

  function trackForms() {
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form, idx){
      if (!form.id) form.id = 'form-' + (idx + 1);
      form.addEventListener('submit', function(){
        pushEvent('form_submit', {form_id: form.id, form_action: form.getAttribute('action') || ''});
      });
    });
  }

  function trackScroll() {
    var marks = [25, 50, 75, 100];
    function onScroll(){
      var doc = document.documentElement;
      var max = Math.max(1, doc.scrollHeight - window.innerHeight);
      var pct = Math.min(100, Math.round((window.scrollY / max) * 100));
      marks.forEach(function(mark){
        var key = 'scroll_' + mark;
        if (pct >= mark && !fired[key]) {
          fired[key] = true;
          pushEvent('scroll_depth', {percent: mark});
        }
      });
    }
    window.addEventListener('scroll', onScroll, {passive:true});
    window.addEventListener('load', onScroll);
  }

  document.addEventListener('DOMContentLoaded', function(){
    preserveUTM();
    trackClicks();
    trackForms();
    trackScroll();
  });
})();
