(function (root) {
  function inScope(row, filters) {
    return ['category', 'region', 'channel'].every(key => filters[key] === 'All' || row[key] === filters[key]);
  }
  function select(data, filters) {
    const key = [filters.category, filters.region, filters.channel].join('|');
    const slice = data.slices[key];
    if (!slice) throw new Error('Unsupported scope');
    const actions = data.actions.filter(row => inScope(row, filters));
    const monthly = Object.values(data.monthly.filter(row => inScope(row, filters)).reduce((out, row) => {
      const value = out[row.month] ||= {month: row.month, revenue: 0, gp: 0, units: 0};
      for (const metric of ['revenue', 'gp', 'units']) value[metric] += row[metric];
      return out;
    }, {})).sort((a,b) => a.month.localeCompare(b.month));
    return {slice, actions, monthly, scenarioTotal: actions.reduce((total, row) => total + row.scenario_gp_eur, 0)};
  }
  function searchActions(rows, search = '', action = 'All') {
    const term = search.trim().toLowerCase();
    return rows.filter(row => (action === 'All' || row.action === action) &&
      [row.product_id, row.product_name, row.region, row.channel, row.reason].join(' ').toLowerCase().includes(term));
  }
  const api = {select, searchActions, inScope};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.RetailModel = api;
})(globalThis);

