"use strict";
const $ = id => document.getElementById(id);
const number = n => new Intl.NumberFormat("pt-BR").format(n);
let state, bot, token, chatBusy = false, lastChat = "", lastNotes = "", lastEvents = "";
const objectives = {hunt:"Caçando",hold:"Em pausa",retreat:"Recuando",resupply:"Reabastecendo",follow:"Seguindo"};
const phases = {idle:"Autonomia ativa.",waiting_hold:"Pausa enviada; aguardando confirmação do servidor.",paused:"Autonomia pausada; combate e cura nativos permanecem ativos.",choose:"Buscando outra ação elegível em uma observação atual.",waiting_action:"Ação enviada; aguardando confirmação do servidor.",failed:"A intervenção parou. Verifique o histórico e use Retomar ou Recuperar rota."};
function notice(message, error=false){$("notice").textContent=message;$("notice").classList.toggle("error",error);$("notice").hidden=false;}
function element(tag, text, cls){const node=document.createElement(tag);node.textContent=text;if(cls)node.className=cls;return node;}
async function command(operation, data={}){
 if(!bot||!token)throw new Error("Aguarde a conexão com o bot.");
 const response=await fetch("/api/command",{method:"POST",headers:{"Content-Type":"application/json","X-Operator-Token":token},body:JSON.stringify({bot:bot.id,operation,...data})});
 const result=await response.json();if(!response.ok)throw new Error(result.error||"A solicitação não foi concluída.");return result;
}
async function action(operation, data={}){
 try{await command(operation,data);notice(({pause:"Pausa solicitada. Acompanhe a confirmação no histórico.",resume:"Retomada solicitada.",recover:"Recuperação solicitada. A rota será redefinida por ações normais do jogo.",retreat:"Recuo solicitado.",avoid:"Rota evitada por 30 minutos; use Recuperar rota para sair da tarefa atual.",note:"Orientação guardada para as próximas decisões.",forget_note:"Orientação removida.",allow_route:"Rota liberada novamente.",automatic:"Proteção atualizada."})[operation]||"Solicitação registrada.");await refresh();return true;}
 catch(error){notice(error.message,true);return false;}
}
function renderChat(){
 const encoded=JSON.stringify(bot.chat);if(encoded===lastChat)return;lastChat=encoded;
 if(!bot.chat.length)return;
 $("conversation").replaceChildren(...bot.chat.map(entry=>{
  const row=element("div",entry.text,"bubble"+(entry.speaker==="human"?" human":""));
  if(entry.speaker==="bot"){
   const reference=new Date((entry.observed_at||entry.at)*1000).toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
   row.append(element("small",`${entry.action_id?"Pedido enviado · confira a confirmação no histórico":"Conversa · nenhuma ordem aplicada"} · Estado consultado às ${reference}`));
  }
  return row;
 }));$("conversation").scrollTop=$("conversation").scrollHeight;
}
function renderNotes(){
 const encoded=JSON.stringify([bot.notes,bot.avoided]);if(encoded===lastNotes)return;lastNotes=encoded;
 $("notes").replaceChildren(...bot.notes.map(note=>{const row=element("div","","saved-row");row.append(element("span",note.text));const button=element("button","Remover","danger link");button.type="button";button.onclick=()=>action("forget_note",{id:note.id});row.append(button);return row;}));
 $("routes").replaceChildren(...Object.entries(bot.avoided).map(([candidate,value])=>{const row=element("div","","saved-row");row.append(element("span",`${candidate} evitada até ${new Date(value.until*1000).toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"})}`));const button=element("button","Liberar","link");button.onclick=()=>action("allow_route",{candidate});row.append(button);return row;}));
}
function renderEvents(){
 const encoded=JSON.stringify(bot.events);if(encoded===lastEvents)return;lastEvents=encoded;
 if(!bot.events.length)return;
 $("events").replaceChildren(...bot.events.map(event=>{const row=element("li",event.text);const stamp=element("time",new Date(event.at*1000).toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit",second:"2-digit"}));row.append(stamp);return row;}));
}
function renderChart(){
 const rows=bot.history;if(!rows.length)return;let low=Math.min(...rows.map(x=>x.xp)),high=Math.max(...rows.map(x=>x.xp));const gap=Math.max(20,high-low);low=Math.max(0,low-gap*.1);high+=gap*.15;
 const span=Math.max(1,rows.at(-1).at-rows[0].at);
 $("xp-line").setAttribute("points",rows.map(x=>`${45+(x.at-rows[0].at)/span*540},${170-(x.xp-low)/(high-low)*150}`).join(" "));
 $("chart-high").textContent=number(Math.ceil(high));$("chart-low").textContent=number(Math.floor(low));
 $("chart-start").textContent=`${Math.max(0,Math.round(span/60))} min`;
 $("chart-gain").textContent=`${rows.at(-1).xp-rows[0].xp>=0?"+":""}${number(rows.at(-1).xp-rows[0].xp)} XP observado`;
}
function render(){
 bot=state.bots[0];token=state.token;
 if(!bot){$("connection").textContent="Aguardando bot";return;}
 const connected=bot.observation_age<=3;
 $("connection").textContent=connected?"Conectado":"Observação antiga";
 $("name").textContent=bot.name;$("level").textContent=number(bot.level);$("xp").textContent=number(bot.xp);$("health").textContent=bot.health+"%";$("potions").textContent=number(bot.potions);
 $("position").textContent=bot.position.join(", ");$("age").textContent=`há ${Math.round(bot.observation_age)} s`;
 $("objective").textContent=bot.control.paused?"Em pausa":objectives[bot.objective]||bot.objective;
 const descriptions={combat:"Há criaturas próximas. Combate e segurança são avaliados antes de qualquer recuperação.",stalled:"Cinco minutos sem movimento, XP ou novos abates. Verifique a tarefa e o histórico.",stale:"O controle está bloqueado até chegar uma observação recente do servidor.",observing:`${bot.objective_defeats} abates neste objetivo · ${bot.no_progress_seconds} s desde o último progresso observado.`};
 $("diagnosis").textContent=(descriptions[bot.diagnosis]||"")+(bot.candidate?` · Rota ${bot.candidate}`:"");
 $("control-state").textContent=phases[bot.control.phase]||phases.idle;
 $("automatic").checked=bot.control.automatic!==false;$("automatic").disabled=!connected;
 document.querySelectorAll("[data-command]").forEach(button=>{const name=button.dataset.command;button.disabled=!connected||(name==="avoid"&&!bot.candidate)||(name==="retreat"&&!bot.actions.some(a=>a.id==="retreat"))||(name==="resume"&&!bot.control.paused&&bot.control.phase==="idle"&&bot.objective!=="hold")||(name==="pause"&&bot.control.paused);});
 const waiting=chatBusy||state.chat_busy.includes(bot.id);$("send").disabled=!connected||waiting;$("send").textContent=waiting?"Respondendo…":"Enviar";
 renderChart();renderChat();renderNotes();renderEvents();
}
async function refresh(){try{const response=await fetch("/api/state",{cache:"no-store"});if(!response.ok)throw new Error("Painel indisponível");state=await response.json();render();}catch(error){$("connection").textContent="Sem conexão";document.querySelectorAll("button").forEach(b=>b.disabled=true);}}
document.querySelectorAll("[data-command]").forEach(button=>button.onclick=()=>action(button.dataset.command));
$("automatic").onchange=()=>action("automatic",{enabled:$("automatic").checked});
$("chat-mode").onchange=()=>$("chat-state").textContent=$("chat-mode").value==="talk"?"Conversar não altera a tarefa atual.":"A ordem só será aplicada se ainda estiver disponível.";
$("chat-form").onsubmit=async event=>{event.preventDefault();chatBusy=true;render();try{const result=await command("chat",{text:$("message").value,act:$("chat-mode").value==="act"});$("message").value="";notice(result.status==="requested"?"Pedido enviado; aguarde o resultado confirmado pelo servidor.":result.status==="not_applied"?"O bot respondeu, mas o estado mudou ou nenhuma nova ação foi aplicada.":"Resposta recebida. A tarefa atual foi mantida.");}catch(error){notice(error.message,true);}finally{chatBusy=false;await refresh();}};
$("note-form").onsubmit=async event=>{event.preventDefault();if(await action("note",{text:$("note").value}))$("note").value="";};
refresh();setInterval(refresh,2000);
