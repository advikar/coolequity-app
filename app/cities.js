/* Every city this site serves, in the order the switchers list them. Shared by
 * all cities' map pages (app/index.html) and checked by scripts/build_site.py
 * against the folders in cities/. Each deploys to <slug>/app/ under the site root. */
window.CE_CITIES=[
  {slug:'contracosta', name:'Contra Costa County', sub:'contracosta/app/'},
  {slug:'bakersfield', name:'Bakersfield',         sub:'bakersfield/app/'},
  {slug:'sanramon',    name:'San Ramon',           sub:'sanramon/app/'},
];
