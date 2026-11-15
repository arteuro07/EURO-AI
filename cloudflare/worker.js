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
    if (request.method === "OPTIONS") return new Response(null, { headers: cors });
    if (url.pathname === "/api/health") {
      return json({ name: "EURO AI", status: "online", version: "0.1.0", brain: "GitHub Actions (integration pending)" });
    }
    if (url.pathname === "/api/chat" && request.method === "POST") {
      if (!env.AUTH_TOKEN) return json({ error: "Authentification non configurée." }, 503);
      const auth = request.headers.get("Authorization") || "";
      if (auth !== "Bearer " + env.AUTH_TOKEN) return json({ error: "Accès refusé." }, 401);
      let body;
      try { body = await request.json(); } catch { return json({ error: "JSON invalide." }, 400); }
      const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
      const message = typeof body.message === "string" ? body.message.trim() : "";
      if (email !== "arteuro07@gmail.com") return json({ error: "Identifiant incorrect." }, 401);
      if (!message) return json({ error: "Le champ message est obligatoire." }, 400);
      if (message.length > 4000) return json({ error: "Message trop long (maximum 4000 caractères)." }, 413);
      return json({ name: "EURO AI", status: "received", message: "Authentification réussie. La passerelle reçoit ta demande ; le cerveau de langage sera connecté à la prochaine étape.", received: message }, 202);
    }
    if (url.pathname === "/") {
      const html = "<!doctype html><html lang=\"fr\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>EURO AI</title><style>*{box-sizing:border-box}body{margin:0;background:#10131b;color:#f4f6fb;font:16px system-ui;display:grid;min-height:100vh;place-items:center;padding:20px}main{width:min(680px,100%);background:#1a2030;border:1px solid #30394d;border-radius:22px;padding:24px}h1{margin:0;font-size:34px}p{color:#aeb8ca}input,textarea{width:100%;border-radius:12px;padding:14px;background:#0f1420;color:white;border:1px solid #3a455b;font:inherit;margin-top:10px}textarea{min-height:110px}button{margin-top:12px;padding:12px 18px;border:0;border-radius:12px;background:#f48120;color:#111;font-weight:700;font-size:15px}#answer{white-space:pre-wrap;background:#111725;border-radius:12px;padding:14px;margin-top:16px;min-height:50px}</style><main><div>● PASSERELLE CLOUDFLARE EN LIGNE</div><h1>EURO AI</h1><p>Connecte-toi pour discuter avec ton assistant.</p><input id=\"email\" type=\"email\" autocomplete=\"username\" placeholder=\"Adresse e-mail\"><input id=\"code\" type=\"password\" autocomplete=\"current-password\" placeholder=\"Code secret\"><textarea id=\"message\" placeholder=\"Écris à EURO AI…\"></textarea><button id=\"send\">Envoyer</button><div id=\"answer\">En attente de connexion.</div><script>const send=document.querySelector('#send'),box=document.querySelector('#answer');send.onclick=async()=>{const email=document.querySelector('#email').value,code=document.querySelector('#code').value,message=document.querySelector('#message').value;send.disabled=true;box.textContent='Vérification…';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+code},body:JSON.stringify({email,message})});const d=await r.json();box.textContent=d.message||d.error||JSON.stringify(d)}catch(e){box.textContent='Erreur réseau : '+e.message}finally{send.disabled=false}};</script></main></html>";
      return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }
    return json({ error: "Route introuvable" }, 404);
  }
};