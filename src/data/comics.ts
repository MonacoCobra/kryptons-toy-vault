import type { CatalogComic, ComicFormat } from "@/lib/types";

type Row = [
  id: string,
  series: string,
  issue: string,
  publisher: string,
  coverDate: string,
  writers: string,
  artists: string,
  description: string,
  msrp: number,
  format: ComicFormat,
  demand: number,
  key: number,
  palette: string,
  extra?: { variant?: string; upc?: string; streetDate?: string; cover?: string },
];

const rows: Row[] = [
  // DC keys & modern
  ["dc-action-1-fac", "Action Comics", "1", "DC Comics", "2018-04-01", "Jerry Siegel", "Joe Shuster", "Facsimile of the 1938 debut of Superman.", 7.99, "facsimile", 1.8, 1, "1e3a8a,e30613,ffd200"],
  ["dc-action-1000", "Action Comics", "1000", "DC Comics", "2018-06-01", "Various", "Various", "Anniversary giant celebrating 80 years of Superman.", 7.99, "single", 2.4, 1, "1e3a8a,e30613,f8fafc"],
  ["dc-action-1050", "Action Comics", "1050", "DC Comics", "2023-02-01", "Phillip Kennedy Johnson", "Riccardo Federici", "Warworld saga fallout. Kal-El back on Earth.", 4.99, "single", 0.8, 0, "0b1f4a,c9a227,e8f0ff"],
  ["dc-superman-75", "Superman", "75", "DC Comics", "1993-01-01", "Dan Jurgens", "Dan Jurgens, Brett Breeding", "The Death of Superman. Black bag polybag era.", 1.75, "single", 80, 1, "111111,e30613,f5f5f5"],
  ["dc-superman-1-2011", "Superman", "1", "DC Comics", "2011-11-01", "George Pérez", "George Pérez", "New 52 Superman #1.", 2.99, "single", 1.6, 1, "1e40af,dc2626,fbbf24"],
  ["dc-allstar-supes-1", "All-Star Superman", "1", "DC Comics", "2006-01-01", "Grant Morrison", "Frank Quitely", "Morrison and Quitely's definitive Superman.", 2.99, "single", 28, 1, "1d4ed8,ef4444,fde047"],
  ["dc-kcome-1", "Kingdom Come", "1", "DC Comics", "1996-05-01", "Mark Waid", "Alex Ross", "Alex Ross painted future of the DCU.", 4.95, "single", 70, 1, "7c2d12,1e3a8a,e5e7eb"],
  ["dc-batman-1-fac", "Batman", "1", "DC Comics", "2019-04-01", "Bill Finger", "Bob Kane", "Facsimile of Batman's first solo title, introducing Joker and Catwoman.", 3.99, "facsimile", 1.4, 1, "111827,facc15,1f2937"],
  ["dc-batman-251", "Batman", "251", "DC Comics", "1973-09-01", "Denny O'Neil", "Neal Adams", "The Joker's first modern appearance. Neal Adams cover.", 0.2, "single", 9000, 1, "14532d,f8fafc,111827"],
  ["dc-batman-404", "Batman", "404", "DC Comics", "1987-02-01", "Frank Miller", "David Mazzucchelli", "Year One part 1.", 0.75, "single", 400, 1, "1f2937,9ca3af,7f1d1d"],
  ["dc-batman-497", "Batman", "497", "DC Comics", "1993-07-01", "Doug Moench", "Jim Aparo", "Knightfall — Bane breaks the Bat.", 1.25, "single", 90, 1, "7f1d1d,111827,e5e7eb"],
  ["dc-batman-608", "Batman", "608", "DC Comics", "2002-12-01", "Jeph Loeb", "Jim Lee", "Hush chapter one. Jim Lee's return to interiors.", 2.25, "single", 35, 1, "1e3a8a,eab308,111827"],
  ["dc-batman-655", "Batman", "655", "DC Comics", "2006-09-01", "Grant Morrison", "Andy Kubert", "Morrison era begins. First Damian Wayne teases.", 2.99, "single", 3.6, 1, "111827,dc2626,f8fafc"],
  ["dc-det-27-fac", "Detective Comics", "27", "DC Comics", "2019-03-01", "Bill Finger", "Bob Kane", "Facsimile of Batman's first appearance.", 7.99, "facsimile", 1.5, 1, "0f172a,eab308,1e3a8a"],
  ["dc-det-38-fac", "Detective Comics", "38", "DC Comics", "2020-05-01", "Bill Finger", "Bob Kane", "Facsimile of Robin's first appearance.", 3.99, "facsimile", 1.2, 1, "1e3a8a,dc2626,f8fafc"],
  ["dc-det-1000", "Detective Comics", "1000", "DC Comics", "2019-03-01", "Various", "Various", "Anniversary issue. Multiple covers.", 9.99, "single", 2.1, 1, "111827,eab308,1e3a8a"],
  ["dc-watchmen-1", "Watchmen", "1", "DC Comics", "1986-09-01", "Alan Moore", "Dave Gibbons", "Who watches the Watchmen. Comedian's funeral.", 1.5, "single", 80, 1, "c2410c,f8fafc,111827"],
  ["dc-sandman-1", "The Sandman", "1", "DC Comics / Vertigo", "1989-01-01", "Neil Gaiman", "Sam Kieth, Mike Dringenberg", "Sleep of the Just. Dream is captured.", 2.0, "single", 70, 1, "111827,7c3aed,fbbf24"],
  ["dc-killingjoke", "Batman: The Killing Joke", "nn", "DC Comics", "1988-07-01", "Alan Moore", "Brian Bolland", "One-shot origin of the Joker. Barbara Gordon is shot.", 3.5, "single", 45, 1, "eab308,111827,dc2626"],
  ["dc-darkknight-1", "Batman: The Dark Knight Returns", "1", "DC Comics", "1986-06-01", "Frank Miller", "Frank Miller, Klaus Janson", "An aging Bruce Wayne returns to the cowl.", 2.95, "single", 55, 1, "7f1d1d,f8fafc,111827"],
  ["dc-jl-1-2011", "Justice League", "1", "DC Comics", "2011-10-01", "Geoff Johns", "Jim Lee", "New 52 Justice League #1.", 3.99, "single", 2.8, 1, "1e3a8a,dc2626,fbbf24"],
  ["dc-abs-martian", "Absolute Martian Manhunter", "1", "DC Comics", "2025-03-01", "Deniz Camp", "Javier Rodríguez", "Absolute Universe Martian Manhunter debut.", 4.99, "single", 1.9, 1, "14532d,ef4444,fde047"],
  ["dc-abs-batman-1", "Absolute Batman", "1", "DC Comics", "2024-10-01", "Scott Snyder", "Nick Dragotta", "No Wayne fortune. Absolute Batman begins.", 4.99, "single", 3.4, 1, "111827,eab308,1e3a8a"],
  ["dc-abs-superman-1", "Absolute Superman", "1", "DC Comics", "2024-11-01", "Jason Aaron", "Rafael Albuquerque", "Kal-El as migrant laborer in the Absolute Universe.", 4.99, "single", 2.2, 1, "1e3a8a,dc2626,fde047"],
  ["dc-ww-1-2011", "Wonder Woman", "1", "DC Comics", "2011-11-01", "Brian Azzarello", "Cliff Chiang", "New 52 Wonder Woman. Gods and clay.", 2.99, "single", 1.4, 1, "dc2626,1e3a8a,fbbf24"],

  // Marvel
  ["mv-af15-fac", "Amazing Fantasy", "15", "Marvel Comics", "2012-04-01", "Stan Lee", "Steve Ditko", "Facsimile of Spider-Man's first appearance.", 3.99, "facsimile", 1.7, 1, "dc2626,1e3a8a,f8fafc"],
  ["mv-asm-1-fac", "The Amazing Spider-Man", "1", "Marvel Comics", "2019-08-01", "Stan Lee", "Steve Ditko", "Facsimile of ASM #1. First J. Jonah Jameson.", 3.99, "facsimile", 1.5, 1, "dc2626,1d4ed8,f8fafc"],
  ["mv-asm-129", "The Amazing Spider-Man", "129", "Marvel Comics", "1974-02-01", "Gerry Conway", "Ross Andru", "First appearance of the Punisher.", 0.25, "single", 2800, 1, "1f2937,dc2626,f8fafc"],
  ["mv-asm-300", "The Amazing Spider-Man", "300", "Marvel Comics", "1988-05-01", "David Michelinie", "Todd McFarlane", "First full appearance of Venom. McFarlane cover.", 1.5, "single", 280, 1, "111827,166534,dc2626"],
  ["mv-asm-361", "The Amazing Spider-Man", "361", "Marvel Comics", "1992-04-01", "David Michelinie", "Mark Bagley", "First full Carnage.", 1.25, "single", 8.5, 1, "7f1d1d,111827,f8fafc"],
  ["mv-asm-700", "The Amazing Spider-Man", "700", "Marvel Comics", "2013-02-01", "Dan Slott", "Humberto Ramos", "Dying Wish. Death of Peter Parker (sort of).", 4.99, "single", 1.6, 1, "dc2626,1e3a8a,f8fafc"],
  ["mv-asm-1-2022", "The Amazing Spider-Man", "1", "Marvel Comics", "2022-04-01", "Zeb Wells", "John Romita Jr.", "Wells / JRJr relaunch.", 5.99, "single", 0.9, 0, "dc2626,1e3a8a,fbbf24"],
  ["mv-uxm-1-fac", "The Uncanny X-Men", "1", "Marvel Comics", "2019-09-01", "Stan Lee", "Jack Kirby", "Facsimile of X-Men #1 (1963).", 3.99, "facsimile", 1.6, 1, "fbbf24,1e3a8a,dc2626"],
  ["mv-gsxm-1", "Giant-Size X-Men", "1", "Marvel Comics", "1975-05-01", "Len Wein", "Dave Cockrum", "The All-New X-Men. Storm, Nightcrawler, Colossus debut.", 0.5, "single", 2800, 1, "1e3a8a,fbbf24,111827"],
  ["mv-uxm-141", "The Uncanny X-Men", "141", "Marvel Comics", "1981-01-01", "Chris Claremont", "John Byrne", "Days of Future Past part 1.", 0.5, "single", 14, 1, "9ca3af,1e3a8a,111827"],
  ["mv-uxm-266", "The Uncanny X-Men", "266", "Marvel Comics", "1990-08-01", "Chris Claremont", "Jim Lee", "First Gambit.", 1.0, "single", 9.2, 1, "7c2d12,a16207,111827"],
  ["mv-hulk-181", "The Incredible Hulk", "181", "Marvel Comics", "1974-11-01", "Len Wein", "Herb Trimpe", "First full Wolverine.", 0.25, "single", 28000, 1, "fbbf24,1e3a8a,111827"],
  ["mv-ff-1-fac", "Fantastic Four", "1", "Marvel Comics", "2018-08-01", "Stan Lee", "Jack Kirby", "Facsimile of Marvel's first family.", 3.99, "facsimile", 1.4, 1, "dc2626,1e3a8a,f8fafc"],
  ["mv-ff-48", "Fantastic Four", "48", "Marvel Comics", "1966-03-01", "Stan Lee", "Jack Kirby", "First appearance of Galactus and the Silver Surfer (cameo).", 0.12, "single", 14000, 1, "7c3aed,1e3a8a,f8fafc"],
  ["mv-ff-550-3d", "Fantastic Four", "550", "Marvel Comics", "2007-11-01", "Dwayne McDuffie", "Paul Pelletier, Rick Magyar", "Reed and Sue return as Black Panther and Storm step down. The original Four, Doctor Strange, the Silver Surfer, Gravity, and Uatu save a dying Eternity.", 2.99, "single", 3.2, 1, "0b1f4a,ea580c,f8fafc", { variant: "3-D Cover", upc: "75960604708855011", streetDate: "2007-10-10", cover: "/covers/mv-ff-550-3d.jpg" }],
  ["mv-avengers-1-fac", "The Avengers", "1", "Marvel Comics", "2018-09-01", "Stan Lee", "Jack Kirby", "Facsimile of Avengers #1.", 3.99, "facsimile", 1.3, 1, "1e3a8a,dc2626,fbbf24"],
  ["mv-avengers-4", "The Avengers", "4", "Marvel Comics", "1964-03-01", "Stan Lee", "Jack Kirby", "Captain America returns.", 0.12, "single", 24, 1, "1e3a8a,dc2626,f8fafc"],
  ["mv-dd-1-1964", "Daredevil", "1", "Marvel Comics", "1964-04-01", "Stan Lee", "Bill Everett", "First appearance of Daredevil.", 0.12, "single", 30, 1, "dc2626,111827,f8fafc"],
  ["mv-dd-168", "Daredevil", "168", "Marvel Comics", "1981-01-01", "Frank Miller", "Frank Miller", "First Elektra. Miller takes over.", 0.5, "single", 11, 1, "dc2626,111827,e5e7eb"],
  ["mv-civilwar-1", "Civil War", "1", "Marvel Comics", "2006-07-01", "Mark Millar", "Steve McNiven", "Superhuman Registration Act. Marvel's 2006 event.", 2.99, "single", 3.2, 1, "1e3a8a,dc2626,f8fafc"],
  ["mv-secretwars-1", "Secret Wars", "1", "Marvel Comics", "1984-05-01", "Jim Shooter", "Mike Zeck", "Beyonder. Battleworld. The original event.", 0.6, "single", 6.8, 1, "7c3aed,111827,fbbf24"],
  ["mv-secretwars-2015-1", "Secret Wars", "1", "Marvel Comics", "2015-05-01", "Jonathan Hickman", "Esad Ribić", "Hickman's final Incursion. Everything dies.", 4.99, "single", 2.1, 1, "111827,eab308,f8fafc"],
  ["mv-immortal-hulk-1", "The Immortal Hulk", "1", "Marvel Comics", "2018-06-01", "Al Ewing", "Joe Bennett", "Horror Hulk. One of the best modern runs.", 4.99, "single", 4.6, 1, "14532d,111827,f8fafc"],
  ["mv-xmen-1-2019", "X-Men", "1", "Marvel Comics", "2019-10-01", "Jonathan Hickman", "Leinil Francis Yu", "House of X / Powers of X follow-up. Krakoa era.", 4.99, "single", 1.8, 1, "dc2626,1e3a8a,fbbf24"],
  ["mv-hox-1", "House of X", "1", "Marvel Comics", "2019-07-01", "Jonathan Hickman", "Pepe Larraz", "Krakoa begins. Mutant nation.", 4.99, "single", 3.8, 1, "fbbf24,1e3a8a,111827"],
  ["mv-ultimate-spidey-1-2024", "Ultimate Spider-Man", "1", "Marvel Comics", "2024-01-01", "Jonathan Hickman", "Marco Checchetto", "Married Peter Parker. Ultimate Universe.", 4.99, "single", 2.6, 1, "dc2626,1e3a8a,f8fafc"],

  // Image / indie
  ["im-spawn-1", "Spawn", "1", "Image Comics", "1992-05-01", "Todd McFarlane", "Todd McFarlane", "Al Simmons returns from hell. Image launch title.", 1.95, "single", 7.2, 1, "111827,7f1d1d,eab308"],
  ["im-spawn-350", "Spawn", "350", "Image Comics", "2024-01-01", "Rory McConville", "Various", "Anniversary issue of the longest-running indie.", 4.99, "single", 1.1, 0, "111827,dc2626,eab308"],
  ["im-twd-1", "The Walking Dead", "1", "Image Comics", "2003-10-01", "Robert Kirkman", "Tony Moore", "Rick Grimes wakes up. First print is a grail.", 2.95, "single", 1600, 1, "365314,111827,e5e7eb"],
  ["im-twd-193", "The Walking Dead", "193", "Image Comics", "2019-07-01", "Robert Kirkman", "Charlie Adlard", "The end of the series.", 3.99, "single", 1.4, 1, "365314,111827,f8fafc"],
  ["im-saga-1", "Saga", "1", "Image Comics", "2012-03-01", "Brian K. Vaughan", "Fiona Staples", "Alana and Marko. Space opera family.", 2.99, "single", 45, 1, "c2410c,1e3a8a,fde68a"],
  ["im-saga-54", "Saga", "54", "Image Comics", "2022-01-01", "Brian K. Vaughan", "Fiona Staples", "Return from hiatus.", 3.99, "single", 1.2, 0, "c2410c,7c3aed,fde68a"],
  ["im-invincible-1", "Invincible", "1", "Image Comics", "2003-01-01", "Robert Kirkman", "Cory Walker", "Mark Grayson. First appearance.", 2.95, "single", 180, 1, "fbbf24,1e3a8a,111827"],
  ["im-invincible-144", "Invincible", "144", "Image Comics", "2018-02-01", "Robert Kirkman", "Ryan Ottley", "Series finale.", 3.99, "single", 1.6, 1, "fbbf24,1e3a8a,dc2626"],
  ["im-east-of-west-1", "East of West", "1", "Image Comics", "2013-03-01", "Jonathan Hickman", "Nick Dragotta", "Four Horsemen in an alternate America.", 2.99, "single", 3.4, 1, "7c2d12,111827,e5e7eb"],
  ["im-deadly-class-1", "Deadly Class", "1", "Image Comics", "2014-01-01", "Rick Remender", "Wes Craig", "Assassin high school, 1980s.", 2.99, "single", 2.8, 1, "111827,dc2626,f8fafc"],
  ["im-radiant-black-1", "Radiant Black", "1", "Image Comics", "2021-02-01", "Kyle Higgins", "Marcelo Costa", "Massive-Verse launch. Regular guy with a cosmic suit.", 3.99, "single", 1.5, 0, "111827,38bdf8,f8fafc"],
  ["im-something-killing-1", "Something is Killing the Children", "1", "Boom! Studios", "2019-09-01", "James Tynion IV", "Werther Dell'Edera", "Erica Slaughter hunts monsters in a small town.", 3.99, "single", 6.4, 1, "111827,7f1d1d,e5e7eb"],
  ["im-department-of-truth-1", "The Department of Truth", "1", "Image Comics", "2020-09-01", "James Tynion IV", "Martin Simmonds", "Conspiracy as physics.", 3.99, "single", 2.9, 1, "dc2626,111827,f8fafc"],
  ["im-monstress-1", "Monstress", "1", "Image Comics", "2015-11-01", "Marjorie Liu", "Sana Takeda", "Epic fantasy. Eisner magnet.", 3.50, "single", 2.2, 1, "1e3a8a,c2410c,fde68a"],
  ["im-paper-girls-1", "Paper Girls", "1", "Image Comics", "2015-10-01", "Brian K. Vaughan", "Cliff Chiang", "1988 paper route. Time travel.", 2.99, "single", 3.1, 1, "f97316,1e3a8a,f8fafc"],
  ["dh-hellboy-seed", "Hellboy: Seed of Destruction", "1", "Dark Horse", "1994-03-01", "Mike Mignola", "Mike Mignola", "First Hellboy miniseries issue.", 2.5, "single", 8.8, 1, "dc2626,111827,eab308"],
  ["dh-sincity-1", "Sin City", "1", "Dark Horse", "1991-04-01", "Frank Miller", "Frank Miller", "The Hard Goodbye begins.", 2.5, "single", 5.5, 1, "111827,f8fafc,dc2626"],
  ["idw-tmnt-1-2011", "Teenage Mutant Ninja Turtles", "1", "IDW Publishing", "2011-08-01", "Kevin Eastman, Tom Waltz", "Dan Duncan", "IDW relaunch of TMNT.", 3.99, "single", 4.2, 1, "166534,1e3a8a,dc2626"],
  ["mirage-tmnt-1-fac", "Teenage Mutant Ninja Turtles", "1", "Mirage / IDW", "2014-05-01", "Kevin Eastman, Peter Laird", "Kevin Eastman, Peter Laird", "Facsimile of the 1984 black-and-white debut.", 4.99, "facsimile", 2.0, 1, "e5e7eb,111827,166534"],
  ["val-xombi-1", "X-O Manowar", "1", "Valiant", "2012-05-01", "Robert Venditti", "Cary Nord", "Aric of Dacia. Valiant relaunch.", 3.99, "single", 1.4, 0, "1e3a8a,c2410c,f8fafc"],
  ["dyn-void-rivals-1", "Void Rivals", "1", "Skybound / Image", "2023-06-01", "Robert Kirkman", "Lorenzo De Felici", "Energon Universe starts here.", 3.99, "single", 3.6, 1, "ea580c,111827,f8fafc"],
  ["dyn-transformers-1", "Transformers", "1", "Skybound / Image", "2023-10-01", "Daniel Warren Johnson", "Daniel Warren Johnson", "Energon Universe Transformers. Instant hit.", 3.99, "single", 4.8, 1, "1e3a8a,dc2626,fbbf24"],
  ["dyn-gi-joe-1", "GI Joe", "1", "Skybound / Image", "2024-01-01", "Joshua Williamson", "Tom Reilly", "Energon Universe GI Joe.", 3.99, "single", 2.3, 1, "14532d,111827,f8fafc"],
  ["boom-once-deadly-1", "Once & Future", "1", "Boom! Studios", "2019-12-01", "Kieron Gillen", "Dan Mora", "King Arthur as a modern horror story.", 3.99, "single", 2.5, 1, "1e3a8a,c2410c,f8fafc"],
  ["abo-eight-billion-1", "Eight Billion Genies", "1", "Image Comics", "2022-09-01", "Charles Soule", "Ryan Browne", "Everyone gets a wish. Everything breaks.", 3.99, "single", 1.7, 0, "7c3aed,111827,fde68a"],
  ["dc-abs-ww-1", "Absolute Wonder Woman", "1", "DC Comics", "2024-12-01", "Kelly Thompson", "Hayden Sherman", "Absolute Universe Wonder Woman. Gods and chains.", 4.99, "single", 2.8, 1, "7f1d1d,eab308,f8fafc"],
  ["dc-abs-flash-1", "Absolute Flash", "1", "DC Comics", "2025-03-01", "Jeff Lemire", "Nick Robles", "Absolute Universe Flash. Speed without the myth.", 4.99, "single", 1.9, 1, "dc2626,fbbf24,111827"],
  ["dc-abs-batman-12", "Absolute Batman", "12", "DC Comics", "2026-09-01", "Scott Snyder", "Nick Dragotta", "Year two of Absolute Batman. The city pushes back.", 4.99, "single", 1.6, 0, "111827,eab308,1e3a8a"],
  ["dc-action-1088", "Action Comics", "1088", "DC Comics", "2026-09-01", "Mark Waid", "Clayton Henry", "Superman faces a new Phantom Zone breakout.", 4.99, "single", 0.9, 0, "1e3a8a,e30613,ffd200"],
  ["dc-batman-158", "Batman", "158", "DC Comics", "2026-09-01", "Chip Zdarsky", "Jorge Jiménez", "Gotham after the latest cowl crisis.", 4.99, "single", 1.1, 0, "111827,eab308,1e3a8a"],
  ["mv-ult-spidey-18", "Ultimate Spider-Man", "18", "Marvel Comics", "2026-09-01", "Jonathan Hickman", "Marco Checchetto", "Married Peter. Ultimate Universe still burning.", 4.99, "single", 1.8, 0, "dc2626,1e3a8a,f8fafc"],
  ["mv-ult-black-panther-1", "Ultimate Black Panther", "1", "Marvel Comics", "2024-02-01", "Bryan Hill", "Stefano Caselli", "Wakanda in the Ultimate Universe.", 4.99, "single", 1.4, 1, "111827,eab308,166534"],
  ["im-saga-72", "Saga", "72", "Image Comics", "2026-08-01", "Brian K. Vaughan", "Fiona Staples", "The family keeps running.", 3.99, "single", 1.3, 0, "c2410c,1e3a8a,fde68a"],
  ["dyn-transformers-24", "Transformers", "24", "Skybound / Image", "2026-09-01", "Daniel Warren Johnson", "Daniel Warren Johnson", "Energon Universe. The war on Earth escalates.", 3.99, "single", 1.7, 0, "1e3a8a,dc2626,fbbf24"],
  ["im-something-killing-45", "Something is Killing the Children", "45", "Boom! Studios", "2026-08-01", "James Tynion IV", "Werther Dell'Edera", "Erica Slaughter is still on the job.", 4.99, "single", 1.2, 0, "111827,7f1d1d,e5e7eb"],
];

function pal(s: string): [string, string, string] {
  const parts = s.split(",").map((p) => `#${p.replace("#", "")}`);
  return [parts[0] ?? "#1e3a8a", parts[1] ?? "#e30613", parts[2] ?? "#f8fafc"];
}

export const COMICS: CatalogComic[] = rows.map(
  ([
    id,
    series,
    issue,
    publisher,
    coverDate,
    writers,
    artists,
    description,
    msrp,
    format,
    demand,
    key,
    palette,
    extra,
  ]) => ({
    id,
    series,
    issue,
    publisher,
    coverDate,
    streetDate: extra?.streetDate,
    writers: writers.split(",").map((w) => w.trim()),
    artists: artists.split(",").map((w) => w.trim()),
    description,
    msrp,
    format,
    variant: extra?.variant,
    upc: extra?.upc,
    demand,
    key: key === 1,
    palette: pal(palette),
    cover: extra?.cover,
  }),
);

export const COMIC_BY_ID: Record<string, CatalogComic> = Object.fromEntries(
  COMICS.map((c) => [c.id, c]),
);

export const COMIC_SERIES = [...new Set(COMICS.map((c) => c.series))].sort();

export const COMIC_PUBLISHERS = [...new Set(COMICS.map((c) => c.publisher))].sort();

function comicKey(c: { series: string; issue: string; publisher: string; variant?: string }) {
  return `${c.series}|${c.issue}|${c.publisher}|${c.variant ?? ""}`.toLowerCase();
}

export function mergeComics(extras: CatalogComic[] = []): CatalogComic[] {
  if (!extras.length) return COMICS;
  const seen = new Set(COMICS.map(comicKey));
  const add = extras.filter((c) => !seen.has(comicKey(c)));
  return add.length ? [...COMICS, ...add] : COMICS;
}

export function comicById(id: string, extras: CatalogComic[] = []): CatalogComic | undefined {
  return COMIC_BY_ID[id] ?? extras.find((c) => c.id === id);
}

export function searchComics(query: string, extras: CatalogComic[] = []): CatalogComic[] {
  const list = mergeComics(extras);
  const q = query.trim().toLowerCase();
  if (!q) return list;
  const issueMatch = q.match(/#?\s*(\d+[a-z]?)$/i);
  return list.filter((c) => {
    const hay = `${c.series} ${c.issue} ${c.publisher} ${c.writers.join(" ")} ${c.artists.join(" ")} ${c.variant ?? ""} ${c.upc ?? ""}`.toLowerCase();
    if (hay.includes(q)) return true;
    if (issueMatch && c.issue === issueMatch[1] && hay.includes(q.replace(issueMatch[0], "").trim())) {
      return true;
    }
    return false;
  });
}

export function recentComics(limit = 10, extras: CatalogComic[] = []): CatalogComic[] {
  return [...mergeComics(extras)].sort((a, b) => {
    const da = a.streetDate ?? a.coverDate;
    const db = b.streetDate ?? b.coverDate;
    return da < db ? 1 : -1;
  }).slice(0, limit);
}

export function comicLabel(c: { series: string; issue: string; variant?: string }) {
  const issue = c.issue.toLowerCase() === "nn" ? "" : ` #${c.issue}`;
  const variant = c.variant ? ` (${c.variant})` : "";
  return `${c.series}${issue}${variant}`;
}
