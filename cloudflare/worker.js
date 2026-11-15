export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    };
    const json = (data, status = 200) => new Response(JSON.stringify(data), {
      status, headers: { ...cors, "Content-Type": "application/json; charset=utf-8" }
    });
    const authorized = () => !!env.AUTH_TOKEN &&
      request.headers.get("Authorization") === "Bearer " + env.AUTH_TOKEN;
    if (request.method === "OPTIONS") return new Response(null, { headers: cors });
    if (url.pathname === "/api/health") {
      return json({
        name: "EURO AI", status: "online", version: "0.2.0",
        brain: "Basic gateway", memory: env.EURO_DB ? "D1 connected" : "D1 unavailable"
      });
    }
    if (url.pathname.startsWith("/api/") && url.pathname !== "/api/health") {
      if (!env.AUTH_TOKEN) return json({ error: "Authentification non configurée." }, 503);
      if (!authorized()) return json({ error: "Accès refusé." }, 401);
      if (!env.EURO_DB) return json({ error: "Base de mémoire indisponible." }, 503);
    }
    if (url.pathname === "/api/chat" && request.method === "POST") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "JSON invalide." }, 400); }
      const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
      const message = typeof body.message === "string" ? body.message.trim() : "";
      if (email !== "arteuro07@gmail.com") return json({ error: "Identifiant incorrect." }, 401);
      if (!message) return json({ error: "Le champ message est obligatoire." }, 400);
      if (message.length > 4000) return json({ error: "Message trop long (maximum 4000 caractères)." }, 413);

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

      const userMessageId = crypto.randomUUID();
      await env.EURO_DB.prepare(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, 'user', ?)"
      ).bind(userMessageId, conversationId, message).run();

      const reply = "J’ai bien reçu ton message et je l’ai enregistré dans ma mémoire. Mon cerveau de langage sera connecté dans une prochaine étape.";
      const assistantMessageId = crypto.randomUUID();
      await env.EURO_DB.prepare(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, 'assistant', ?)"
      ).bind(assistantMessageId, conversationId, reply).run();
      await env.EURO_DB.prepare(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?"
      ).bind(conversationId).run();

      return json({
        name: "EURO AI", status: "saved", conversation_id: conversationId,
        reply, memory: "saved"
      }, 200);
    }
    if (url.pathname === "/api/conversations" && request.method === "GET") {
      const result = await env.EURO_DB.prepare(
        "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC LIMIT 50"
      ).all();
      return json({ conversations: result.results || [] });
    }
    const messagesMatch = url.pathname.match(/^\/api\/conversations\/([a-f0-9-]+)\/messages$/i);
    if (messagesMatch && request.method === "GET") {
      const conversationId = messagesMatch[1];
      const result = await env.EURO_DB.prepare(
        "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC, rowid ASC"
      ).bind(conversationId).all();
      return json({ conversation_id: conversationId, messages: result.results || [] });
    }
    if (url.pathname === "/") {
      const html = "<!doctype html><html lang=\"fr\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>EURO AI</title><style>*{box-sizing:border-box}body{margin:0;background:#10131b;color:#f4f6fb;font:16px system-ui;display:grid;min-height:100vh;place-items:center;padding:20px}main{width:min(680px,100%);background:#1a2030;border:1px solid #30394d;border-radius:22px;padding:24px}h1{margin:0;font-size:34px}p{color:#aeb8ca}input,textarea{width:100%;border-radius:12px;padding:14px;background:#0f1420;color:white;border:1px solid #3a455b;font:inherit;margin-top:10px}textarea{min-height:110px}button{margin-top:12px;padding:12px 18px;border:0;border-radius:12px;background:#f48120;color:#111;font-weight:700;font-size:15px}#answer{white-space:pre-wrap;background:#111725;border-radius:12px;padding:14px;margin-top:16px;min-height:50px}</style><main><div>● PASSERELLE CLOUDFLARE EN LIGNE</div><h1>EURO AI</h1><p>Connecte-toi pour discuter avec ton assistant.</p><input id=\"email\" type=\"email\" autocomplete=\"username\" placeholder=\"Adresse e-mail\"><input id=\"code\" type=\"password\" autocomplete=\"current-password\" placeholder=\"Code secret\"><textarea id=\"message\" placeholder=\"Écris à EURO AI…\"></textarea><button id=\"send\">Envoyer</button><div id=\"answer\">En attente de connexion.</div><script>let conversationId=null;const send=document.querySelector('#send'),box=document.querySelector('#answer');send.onclick=async()=>{const email=document.querySelector('#email').value,code=document.querySelector('#code').value,message=document.querySelector('#message').value;send.disabled=true;box.textContent='Enregistrement…';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+code},body:JSON.stringify({email,message,conversation_id:conversationId})});const d=await r.json();if(!r.ok)throw new Error(d.error||'Erreur serveur');conversationId=d.conversation_id;box.textContent=d.reply;document.querySelector('#message').value=''}catch(e){box.textContent='Erreur : '+e.message}finally{send.disabled=false}};</script></main></html>";
      return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }
    return json({ error: "Route introuvable" }, 404);
  }
};