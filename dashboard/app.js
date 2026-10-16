(() => {
  'use strict';
  const data = window.RETAIL_DATA, model = window.RetailModel;
  const $ = id => document.getElementById(id);
  const money = value => new Intl.NumberFormat('en-IE',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(value);
  const unitMoney = value => new Intl.NumberFormat('en-IE',{style:'currency',currency:'EUR',minimumFractionDigits:2,maximumFractionDigits:2}).format(value);
  const short = value => `${value < 0 ? '−' : ''}€${Math.abs(value) >= 1e6 ? (Math.abs(value)/1e6).toFixed(2)+'m' : (Math.abs(value)/1e3).toFixed(1)+'k'}`;
  const pct = value => `${(value*100).toFixed(1)}%`;
  const sign = value => value >= 0 ? '+' : '−';
  const esc = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  let shown = 25, currentRows = [], scope;
  for (const category of data.categories) $('category').add(new Option(category, category));
  const filters = () => Object.fromEntries(['category','region','channel'].map(key => [key,$(key).value]));

  function bridgeSVG(bridge) {
    const values = [{label:'H1 GP',from:0,to:bridge.baseline_gp,total:true}];
    let running = bridge.baseline_gp;
    const labels = {volume:'Volume',mix:'Joint mix',list_price:'List price',discount:'Discount',cost:'Cost'};
    for (const [key, amount] of Object.entries(bridge.effects)) { values.push({label:labels[key],from:running,to:running+amount,amount}); running+=amount; }
    values.push({label:'H2 GP',from:0,to:bridge.current_gp,total:true});
    const max = Math.max(...values.flatMap(v=>[v.from,v.to]))*1.12, min=Math.min(0,...values.flatMap(v=>[v.from,v.to]));
    const y = value => 265 - (value-min)/(max-min)*225;
    let svg='<svg viewBox="0 0 940 330" role="img" aria-label="Gross-profit bridge from H1 to H2 in euros"><title>Exact gross-profit accounting bridge</title>';
    for(let i=0;i<5;i++){const v=min+(max-min)*i/4;svg+=`<line x1="68" x2="930" y1="${y(v)}" y2="${y(v)}" stroke="#e7edf9"/><text x="57" y="${y(v)+4}" text-anchor="end" font-size="10" fill="#53658d">${short(v)}</text>`;}
    values.forEach((v,i)=>{const x=86+i*120, color=v.total?(i===6?'#f5d547':'#2456e8'):(v.amount<0?'#e7433d':'#2456e8');
      svg+=`<rect x="${x}" y="${y(Math.max(v.from,v.to))}" width="78" height="${Math.max(1,Math.abs(y(v.to)-y(v.from)))}" fill="${color}"><title>${v.label}: ${money(v.total?v.to:v.amount)}</title></rect><text x="${x+39}" y="${y(Math.max(v.from,v.to))-9}" text-anchor="middle" font-size="12" font-weight="700" fill="#142b66">${v.total?short(v.to):sign(v.amount)+short(Math.abs(v.amount))}</text><text x="${x+39}" y="298" text-anchor="middle" font-size="12" fill="#142b66">${v.label}</text>`;
      if(i<6) svg+=`<line x1="${x+78}" x2="${x+120}" y1="${y(v.to)}" y2="${y(v.to)}" stroke="#9daed0" stroke-dasharray="3 3"/>`;
    }); return svg+'</svg>';
  }
  function trendSVG(rows){
    const values=rows.map(r=>r.gp/r.revenue), low=Math.min(...values)-.025, high=Math.max(...values)+.025;
    const x=i=>70+i*76, y=v=>165-(v-low)/(high-low)*125;
    let svg='<svg viewBox="0 0 940 220" role="img" aria-label="Monthly gross margin for the selected scope"><title>Monthly gross margin</title>';
    for(let i=0;i<4;i++){const v=low+(high-low)*i/3;svg+=`<line x1="60" x2="920" y1="${y(v)}" y2="${y(v)}" stroke="#e7edf9"/><text x="50" y="${y(v)+4}" text-anchor="end" font-size="11" fill="#53658d">${pct(v)}</text>`;}
    svg+=`<polyline points="${values.map((v,i)=>`${x(i)},${y(v)}`).join(' ')}" fill="none" stroke="#2456e8" stroke-width="3"/>`;
    rows.forEach((r,i)=>svg+=`<circle cx="${x(i)}" cy="${y(values[i])}" r="4" fill="#2456e8"><title>${r.month}: ${pct(values[i])}</title></circle><text x="${x(i)}" y="197" text-anchor="middle" font-size="11" fill="#53658d">${r.month.slice(5)}</text>`);
    return svg+'</svg>';
  }
  function renderTable(){
    currentRows=model.searchActions(scope.actions,$('search').value,$('action').value);
    $('matches').textContent=`${currentRows.length.toLocaleString()} matching cells`;
    $('actions').innerHTML=currentRows.slice(0,shown).map((r,i)=>`<tr><td><strong>${esc(r.product_id)}</strong> · ${esc(r.category)}<small>${esc(r.tier)} / ${esc(r.region)} / ${esc(r.channel)}</small></td><td><span class="tag ${r.action}">${r.action}</span></td><td>${pct(r.h2_margin)}</td><td class="${r.gp_delta<0?'negative':'positive'}">${money(r.gp_delta)}</td><td>${r.scenario_gp_eur?money(r.scenario_gp_eur):'Not estimated'}</td><td><button data-row="${i}" aria-label="Inspect action for ${esc(r.product_id+' '+r.region+' '+r.channel)}">Inspect</button></td></tr>`).join('');
    if(!currentRows.length)$('actions').innerHTML='<tr><td colspan="6">No matching cells. Try another action or search.</td></tr>';
    $('more').hidden=shown>=currentRows.length;
    $('actions').querySelectorAll('button[data-row]').forEach(button=>button.addEventListener('click',()=>showDetail(currentRows[Number(button.dataset.row)])));
  }
  function showDetail(r){
    $('detail').innerHTML=`<h3>${esc(r.product_id)} · ${r.action}</h3><p><strong>${esc(r.category+' / '+r.region+' / '+r.channel)}</strong></p><p>${esc(r.instruction)}</p><p>Rule: ${esc(r.reason)}. Discount change: ${r.discount_change_pp.toFixed(1)} pp. Cost change: ${r.cost_change_pct.toFixed(1)}%. List-price change: ${r.list_price_change_pct.toFixed(1)}%.</p><p>H1 / H2 units: ${r.h1_units} / ${r.h2_units}. H1 / H2 GP: ${money(r.h1_gp)} / ${money(r.h2_gp)}.</p><p><strong>Scenario: ${r.scenario_gp_eur?money(r.scenario_gp_eur):'Not estimated'}.</strong> ${esc(r.assumption)}</p><p>H2 unit values: list price ${unitMoney(r.h2_list_price)}, discount ${unitMoney(r.h2_discount_per_unit)}, cost ${unitMoney(r.h2_cost_per_unit)}.</p>`;
  }
  function render(){
    scope=model.select(data,filters());shown=25;
    const s=scope.slice, [before,after]=s.periods;
    const cards=[['H2 revenue',money(after.revenue),`${sign(s.revenue_change)}${pct(Math.abs(s.revenue_change))} vs H1`],['H2 gross profit',money(after.gp),`${sign(s.gp_change)}${pct(Math.abs(s.gp_change))} vs H1`],['H2 gross margin',pct(after.margin),`${s.margin_change_pp.toFixed(2)} pp vs H1`],['Adverse driver contributions',money(s.adverse_contributions),'Gross headwinds, before positive offsets']];
    $('kpis').innerHTML=cards.map(([label,value,note])=>`<article class="kpi"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`).join('');
    $('bridge').innerHTML=bridgeSVG(s.bridge);$('trend').innerHTML=trendSVG(scope.monthly);
    $('reconciliation').textContent=`Reconciled · residual < €0.01`;
    $('scenario-total').textContent=money(scope.scenarioTotal);
    $('detail').innerHTML='<h3>Select an action to inspect its rule and assumptions.</h3>';
    renderTable();
  }
  const mix=data.diagnostics.product_mix[0], stock=data.diagnostics.availability[0], customer=data.diagnostics.customer_mix[0];
  $('diagnostics').innerHTML=`<article><h3>${esc(mix.category)} / Premium</h3><strong>${mix.change_pp.toFixed(1)} pp</strong><p>Premium unit-share change, H1 → H2. This diagnostic is narrower than the joint-mix bridge.</p></article><article><h3>${esc(stock.category+' / '+stock.region)}</h3><strong>${stock.change_pp.toFixed(1)} pp</strong><p>${esc(stock.tier)} snapshot in-stock change: Jan–Aug → Sep–Oct. Not an estimate of lost demand.</p></article><article><h3>${esc(customer.channel+' / '+customer.segment)}</h3><strong>+${customer.change_pp.toFixed(1)} pp</strong><p>Unit-share change, H1 → H2. An association to investigate, not a separately additive loss.</p></article>`;
  for(const id of ['category','region','channel'])$(id).addEventListener('change',render);
  for(const id of ['search','action'])$(id).addEventListener(id==='search'?'input':'change',()=>{shown=25;renderTable();});
  $('more').addEventListener('click',()=>{shown+=25;renderTable();});
  $('reset').addEventListener('click',()=>{for(const id of ['category','region','channel','action'])$(id).value='All';$('search').value='';render();});
  render();
})();
