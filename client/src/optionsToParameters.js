export default (opts) => {
  return Object.keys(opts).map(d => `${d}=${opts[d]}`).join('&');
}
