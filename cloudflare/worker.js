export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    };
    const json = (data, status = 200) => new Response(JSON.stringify(data), {
      status, headers: { ...cors, "Content-Type": "application/json; charset=utf-8" }
    });
    const authorized = () => !!env.AUTH_TOKEN &&
      request.headers.get("Authorization") === "Bearer " + env.AUTH_TOKEN;
    const defaults = {
      owner_instructions: ["Répondre en français par défaut."],
      allowed_categories: [],
      blocked_categories: [],
      custom_rules: [],
      confirmation_required: true,
      language: "fr"
    };
    const readSettings = async () => {
      const row = await env.EURO_DB.prepare(
        "SELECT settings_json FROM owner_settings WHERE id = 'owner'"
      ).first();
      if (!row) return defaults;
      try { return { ...defaults, ...JSON.parse(row.settings_json) }; }
      catch { return defaults; }
    };
    if (request.method === "OPTIONS") return new Response(null, { headers: cors });
    if (url.pathname === "/api/health") {
      return json({
        name: "EURO AI", status: "online", version: "0.3.0",
        brain: "Basic gateway", memory: env.EURO_DB ? "D1 connected" : "D1 unavailable",
        owner_panel: "enabled"
      });
    }
    if (url.pathname.startsWith("/api/") && url.pathname !== "/api/health") {
      if (!env.AUTH_TOKEN) return json({ error: "Authentification non configurée." }, 503);
      if (!authorized()) return json({ error: "Accès refusé." }, 401);
      if (!env.EURO_DB) return json({ error: "Base de mémoire indisponible." }, 503);
    }
    if (url.pathname === "/api/settings" && request.method === "GET") {
      return json({ settings: await readSettings() });
    }
    if (url.pathname === "/api/settings" && request.method === "PUT") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "JSON invalide." }, 400); }
      const input = body && body.settings;
      if (!input || typeof input !== "object" || Array.isArray(input)) {
        return json({ error: "Réglages invalides." }, 400);
      }
      const cleanList = (value, label) => {
        if (!Array.isArray(value) || value.length > 50 ||
            value.some(x => typeof x !== "string" || !x.trim() || x.length > 500)) {
          throw new Error("Le champ " + label + " doit contenir au maximum 50 lignes de 500 caractères.");
        }
        return value.map(x => x.trim());
      };
      let settings;
      try {
        settings = {
          owner_instructions: cleanList(input.owner_instructions, "instructions"),
          allowed_categories: cleanList(input.allowed_categories, "catégories autorisées"),
          blocked_categories: cleanList(input.blocked_categories, "catégories bloquées"),
          custom_rules: cleanList(input.custom_rules, "règles personnalisées"),
          confirmation_required: input.confirmation_required === true,
          language: ["fr", "en"].includes(input.language) ? input.language : "fr"
        };
      } catch (e) { return json({ error: e.message }, 400); }
      await env.EURO_DB.prepare(
        "INSERT INTO owner_settings (id, settings_json, updated_at) VALUES ('owner', ?, CURRENT_TIMESTAMP) ON CONFLICT(id) DO UPDATE SET settings_json = excluded.settings_json, updated_at = CURRENT_TIMESTAMP"
      ).bind(JSON.stringify(settings)).run();
      return json({ status: "saved", settings });
    }
    if (url.pathname === "/api/chat" && request.method === "POST") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "JSON invalide." }, 400); }
      const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
      const message = typeof body.message === "string" ? body.message.trim() : "";
      if (email !== "arteuro07@gmail.com") return json({ error: "Identifiant incorrect." }, 401);
      if (!message) return json({ error: "Le champ message est obligatoire." }, 400);
      if (message.length > 4000) return json({ error: "Message trop long (maximum 4000 caractères)." }, 413);
      const settings = await readSettings();
      const blocked = settings.blocked_categories.find(term => message.toLowerCase().includes(term.toLowerCase()));
      let conversationId = typeof body.conversation_id === "string" ? body.conversation_id : "";
      if (conversationId) {
        const existing = await env.EURO_DB.prepare(
          "SELECT id FROM conversations WHERE id = ?"
        ).bind(conversationId).first();
        if (!existing) return json({ error: "Conversation introuvable." }, 404);
      } else {
        conversationId = crypto.randomUUID();
        const title = message.replace(/\s+/g, " ").slice(0, 70) || "Nouvelle conversation";
        await env.EURO_DB.prepare(
          "INSERT INTO conversations (id, title) VALUES (?, ?)"
        ).bind(conversationId, title).run();
      }
      await env.EURO_DB.prepare(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, 'user', ?)"
      ).bind(crypto.randomUUID(), conversationId, message).run();
      const reply = blocked
        ? "Ta règle personnelle bloque cette demande : " + blocked
        : "J’ai bien reçu ton message et je l’ai enregistré. Mon cerveau de langage sera connecté dans une prochaine étape.";
      await env.EURO_DB.prepare(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, 'assistant', ?)"
      ).bind(crypto.randomUUID(), conversationId, reply).run();
      await env.EURO_DB.prepare(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?"
      ).bind(conversationId).run();
      return json({ name: "EURO AI", status: "saved", conversation_id: conversationId, reply, memory: "saved" });
    }
    if (url.pathname === "/api/conversations" && request.method === "GET") {
      const result = await env.EURO_DB.prepare(
        "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC LIMIT 50"
      ).all();
      return json({ conversations: result.results || [] });
    }
    const messagesMatch = url.pathname.match(/^\/api\/conversations\/([a-f0-9-]+)\/messages$/i);
    if (messagesMatch && request.method === "GET") {
      const result = await env.EURO_DB.prepare(
        "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC, rowid ASC"
      ).bind(messagesMatch[1]).all();
      return json({ conversation_id: messagesMatch[1], messages: result.results || [] });
    }
    if (url.pathname === "/") {
      const html = `<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EURO AI — Contrôle</title><style>
      *{box-sizing:border-box}body{margin:0;background:#10131b;color:#f4f6fb;font:15px system-ui;min-height:100vh;padding:18px}
      main{width:min(760px,100%);margin:auto;background:#1a2030;border:1px solid #30394d;border-radius:20px;padding:20px}
      h1{margin:0;font-size:30px}h2{font-size:19px;margin:22px 0 8px}p,.muted{color:#aeb8ca}
      input,textarea,select{width:100%;border-radius:10px;padding:12px;background:#0f1420;color:white;border:1px solid #3a455b;font:inherit;margin:7px 0 12px}
      textarea{min-height:105px;resize:vertical}button{padding:11px 16px;border:0;border-radius:10px;background:#f48120;color:#111;font-weight:700;font-size:14px;margin:5px 5px 5px 0}
      button.secondary{background:#30394d;color:white}button:disabled{opacity:.5}.tab{border-bottom:1px solid #354057;padding-bottom:12px;margin:15px 0}
      .panel{background:#121927;border:1px solid #30394d;border-radius:14px;padding:14px;margin-top:14px}.row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
      label{display:block;color:#dce3ef;font-weight:600;margin-top:10px}small{color:#9eabc0}#answer,#status{white-space:pre-wrap;background:#111725;border-radius:10px;padding:12px;margin-top:12px;min-height:36px}
      .check{width:auto;margin-right:8px}.checklabel{display:flex;align-items:center;font-weight:500}
      </style><main><div class="muted">● EURO AI · ESPACE PROPRIÉTAIRE</div><h1>EURO AI</h1><p>Tu contrôles les règles et les préférences de ton assistant.</p>
      <section class="panel"><h2>Connexion</h2><label>Adresse e-mail</label><input id="email" type="email" autocomplete="username" value="arteuro07@gmail.com"><label>Code secret</label><input id="code" type="password" autocomplete="current-password" placeholder="Ton code secret"><div class="row"><button id="connect">Se connecter</button><span id="status">Non connecté</span></div></section>
      <section id="workspace" hidden>
      <div class="tab"><button class="secondary" id="tabRules">Mes règles</button><button class="secondary" id="tabChat">Discussion</button></div>
      <section id="rulesPanel" class="panel"><h2>Mes règles personnelles</h2><p class="muted">Une règle par ligne. Tu peux ajouter ou supprimer librement tes propres règles.</p>
      <label>Langue</label><select id="language"><option value="fr">Français</option><option value="en">English</option></select>
      <label>Instructions personnelles</label><textarea id="instructions" placeholder="Ex. Réponds de façon directe…"></textarea>
      <label>Catégories autorisées</label><textarea id="allowed" placeholder="Une catégorie par ligne"></textarea>
      <label>Catégories bloquées</label><textarea id="blocked" placeholder="Une catégorie ou expression par ligne"></textarea>
      <label>Règles personnalisées</label><textarea id="custom" placeholder="Ajoute ici tes propres règles"></textarea>
      <label class="checklabel"><input class="check" id="confirm" type="checkbox"> Demander une confirmation avant les actions</label>
      <div class="row"><button id="save">Enregistrer mes réglages</button><button class="secondary" id="reload">Recharger</button></div>
      <small>Les réglages sont sauvegardés dans ta base EURO AI (D1).</small></section>
      <section id="chatPanel" class="panel" hidden><h2>Discussion</h2><textarea id="message" placeholder="Écris à EURO AI…"></textarea><button id="send">Envoyer</button><div id="answer">En attente.</div></section>
      </section></main><script>
      let token='',conversationId=null;const $=id=>document.getElementById(id);
      const auth=()=>({'Content-Type':'application/json','Authorization':'Bearer '+token});
      const lines=id=>$(id).value.split('\\n').map(x=>x.trim()).filter(Boolean);
      async function api(path,opts={}){const r=await fetch(path,{...opts,headers:{...auth(),...(opts.headers||{})}});const d=await r.json();if(!r.ok)throw new Error(d.error||'Erreur serveur');return d}
      function showSettings(s){$('language').value=s.language||'fr';$('instructions').value=(s.owner_instructions||[]).join('\\n');$('allowed').value=(s.allowed_categories||[]).join('\\n');$('blocked').value=(s.blocked_categories||[]).join('\\n');$('custom').value=(s.custom_rules||[]).join('\\n');$('confirm').checked=s.confirmation_required!==false}
      async function load(){const d=await api('/api/settings');showSettings(d.settings);$('status').textContent='Connecté · réglages chargés'}
      $('connect').onclick=async()=>{token=$('code').value;if(!token){$('status').textContent='Entre ton code secret';return}try{await load();$('workspace').hidden=false}catch(e){token='';$('status').textContent=e.message}}
      $('save').onclick=async()=>{try{$('save').disabled=true;const settings={language:$('language').value,owner_instructions:lines('instructions'),allowed_categories:lines('allowed'),blocked_categories:lines('blocked'),custom_rules:lines('custom'),confirmation_required:$('confirm').checked};const d=await api('/api/settings',{method:'PUT',body:JSON.stringify({settings})});showSettings(d.settings);$('status').textContent='Réglages enregistrés ✓'}catch(e){$('status').textContent='Erreur : '+e.message}finally{$('save').disabled=false}}
      $('reload').onclick=()=>load().catch(e=>$('status').textContent=e.message);
      $('tabRules').onclick=()=>{$('rulesPanel').hidden=false;$('chatPanel').hidden=true};
      $('tabChat').onclick=()=>{$('rulesPanel').hidden=true;$('chatPanel').hidden=false};
      $('send').onclick=async()=>{try{$('send').disabled=true;$('answer').textContent='Enregistrement…';const d=await api('/api/chat',{method:'POST',body:JSON.stringify({email:$('email').value,message:$('message').value,conversation_id:conversationId})});conversationId=d.conversation_id;$('answer').textContent=d.reply;$('message').value=''}catch(e){$('answer').textContent='Erreur : '+e.message}finally{$('send').disabled=false}};
      </script></html>`;
      return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }
    return json({ error: "Route introuvable" }, 404);
  }
};