const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const model = require('./dashboard/model.js');
const data = JSON.parse(fs.readFileSync(path.join(__dirname,'outputs/report.json'),'utf8'));
let checked=0;
for(const key of Object.keys(data.slices)){
  const [category,region,channel]=key.split('|');
  const scope=model.select(data,{category,region,channel});
  assert(Math.abs(scope.actions.reduce((s,r)=>s+r.h2_gp,0)-scope.slice.periods[1].gp)<.01,key);
  for(const [i,period] of ['H1','H2'].entries()){
    const monthly=scope.monthly.filter(row=>(row.month<'2025-07'?'H1':'H2')===period);
    assert(Math.abs(monthly.reduce((s,r)=>s+r.gp,0)-scope.slice.periods[i].gp)<.01,key+' monthly GP');
    assert(Math.abs(monthly.reduce((s,r)=>s+r.revenue,0)-scope.slice.periods[i].revenue)<.01,key+' monthly revenue');
  }
  assert(scope.actions.every(row=>model.inScope(row,{category,region,channel})));
  checked++;
}
assert.equal(model.searchActions(data.actions,'definitely-not-a-product').length,0);
assert(model.searchActions(data.actions,'p0001').every(row=>row.product_id==='P0001'));
assert(model.searchActions(data.actions,'','MODIFY').every(row=>row.action==='MODIFY'));
assert.throws(()=>model.select(data,{category:'Unknown',region:'All',channel:'All'}));
console.log(`Dashboard model verified: ${checked} scopes, monthly/KPI reconciliation, search and action filters.`);

