import type { CatalogFigure, CompanyId, ItemKind } from "@/lib/types";

type Row = [
  id: string,
  name: string,
  subtitle: string,
  line: string,
  company: CompanyId,
  kind: ItemKind,
  releaseDate: string,
  msrp: number,
  scale: string,
  demand: number,
  tags: string,
  extra?: { sku?: string; exclusive?: string },
];

const rows: Row[] = [
  // Hasbro — Marvel Legends
  ["ml-wolverine-97", "Wolverine", "X-Men '97", "Marvel Legends", "hasbro", "figure", "2024-03-12", 24.99, '6"', 1.35, "marvel,x-men", { sku: "F9115" }],
  ["ml-storm-97", "Storm", "X-Men '97", "Marvel Legends", "hasbro", "figure", "2024-03-12", 24.99, '6"', 1.2, "marvel,x-men"],
  ["ml-magneto-97", "Magneto", "X-Men '97", "Marvel Legends", "hasbro", "figure", "2024-07-01", 24.99, '6"', 1.25, "marvel,x-men"],
  ["ml-cyclops-97", "Cyclops", "X-Men '97", "Marvel Legends", "hasbro", "figure", "2024-07-01", 24.99, '6"', 1.1, "marvel,x-men"],
  ["ml-gambit-97", "Gambit", "X-Men '97", "Marvel Legends", "hasbro", "figure", "2024-11-05", 24.99, '6"', 1.55, "marvel,x-men"],
  ["ml-rogue-97", "Rogue", "X-Men '97", "Marvel Legends", "hasbro", "figure", "2024-11-05", 24.99, '6"', 1.4, "marvel,x-men"],
  ["ml-deadpool-bib", "Deadpool", "Back in Black", "Marvel Legends", "hasbro", "figure", "2024-07-20", 24.99, '6"', 1.15, "marvel"],
  ["ml-spiderman-af", "Spider-Man", "Amazing Fantasy", "Marvel Legends", "hasbro", "figure", "2023-08-15", 24.99, '6"', 1.3, "marvel,spider-man"],
  ["ml-venom-sm2", "Venom", "Marvel's Spider-Man 2", "Marvel Legends", "hasbro", "figure", "2023-10-01", 24.99, '6"', 0.95, "marvel,spider-man"],
  ["ml-cap-sam", "Captain America", "Sam Wilson", "Marvel Legends", "hasbro", "figure", "2024-02-10", 24.99, '6"', 0.85, "marvel"],
  ["ml-ironman-m20", "Iron Man", "Model 20", "Marvel Legends", "hasbro", "figure", "2023-11-12", 32.99, '6"', 1.05, "marvel"],
  ["ml-strange-mom", "Doctor Strange", "Multiverse of Madness", "Marvel Legends", "hasbro", "figure", "2022-05-01", 22.99, '6"', 0.7, "marvel"],
  ["ml-moon-knight", "Moon Knight", "Midnight Suns", "Marvel Legends", "hasbro", "figure", "2022-09-20", 24.99, '6"', 1.45, "marvel", { exclusive: "GameStop" }],
  ["ml-secret-wars-spidey", "Spider-Man", "Secret Wars", "Marvel Legends", "hasbro", "figure", "2024-05-18", 24.99, '6"', 1.6, "marvel,spider-man"],
  ["ml-knull", "Knull", "King in Black", "Marvel Legends", "hasbro", "figure", "2021-10-04", 49.99, '6"', 1.8, "marvel", { exclusive: "Hasbro Pulse" }],

  // Hasbro — Black Series
  ["bs-vader-esb", "Darth Vader", "The Empire Strikes Back", "Star Wars Black Series", "hasbro", "figure", "2020-09-01", 24.99, '6"', 1.1, "star-wars"],
  ["bs-luke-bespin", "Luke Skywalker", "Bespin", "Star Wars Black Series", "hasbro", "figure", "2021-04-12", 24.99, '6"', 1.25, "star-wars"],
  ["bs-ahsoka", "Ahsoka Tano", "Peridea", "Star Wars Black Series", "hasbro", "figure", "2023-08-22", 24.99, '6"', 1.2, "star-wars"],
  ["bs-mando-beskar", "Din Djarin", "Beskar Armor", "Star Wars Black Series", "hasbro", "figure", "2021-02-01", 24.99, '6"', 0.9, "star-wars"],
  ["bs-armorer", "The Armorer", "The Mandalorian", "Star Wars Black Series", "hasbro", "figure", "2021-11-15", 24.99, '6"', 1.35, "star-wars"],
  ["bs-grogu-force", "Grogu", "Force Wielding", "Star Wars Black Series", "hasbro", "figure", "2022-06-01", 19.99, '6"', 0.8, "star-wars"],
  ["bs-andor", "Cassian Andor", "Andor", "Star Wars Black Series", "hasbro", "figure", "2022-09-10", 24.99, '6"', 0.75, "star-wars"],
  ["bs-thrawn", "Grand Admiral Thrawn", "Ahsoka", "Star Wars Black Series", "hasbro", "figure", "2023-09-05", 24.99, '6"', 1.5, "star-wars"],

  // Hasbro — GI Joe / Transformers / Rangers
  ["joe-snake-eyes", "Snake Eyes", "Commando", "GI Joe Classified", "hasbro", "figure", "2020-03-01", 19.99, '6"', 1.4, "gi-joe"],
  ["joe-storm-shadow", "Storm Shadow", "Arashikage", "GI Joe Classified", "hasbro", "figure", "2020-07-15", 19.99, '6"', 1.55, "gi-joe"],
  ["joe-cobra-commander", "Cobra Commander", "Hooded", "GI Joe Classified", "hasbro", "figure", "2021-01-20", 22.99, '6"', 1.3, "gi-joe"],
  ["joe-destro", "Destro", "M.A.R.S. Industries", "GI Joe Classified", "hasbro", "figure", "2022-05-08", 49.99, '6"', 1.15, "gi-joe"],
  ["ss-optimus-102", "Optimus Prime", "Bumblebee Movie", "Transformers Studio Series", "hasbro", "figure", "2023-06-01", 54.99, "Voyager", 1.2, "transformers"],
  ["ss-megatron", "Megatron", "Rise of the Beasts", "Transformers Studio Series", "hasbro", "figure", "2023-06-01", 49.99, "Voyager", 0.95, "transformers"],
  ["ss-bumblebee", "Bumblebee", "WWII", "Transformers Studio Series", "hasbro", "figure", "2022-11-01", 29.99, "Deluxe", 0.85, "transformers"],
  ["pr-red-lc", "Red Ranger", "Mighty Morphin", "Lightning Collection", "hasbro", "figure", "2019-08-01", 19.99, '6"', 1.7, "power-rangers"],
  ["pr-white-lc", "White Ranger", "Mighty Morphin", "Lightning Collection", "hasbro", "figure", "2020-02-01", 22.99, '6"', 2.1, "power-rangers"],
  ["pr-green-lc", "Green Ranger", "Mighty Morphin", "Lightning Collection", "hasbro", "figure", "2019-11-01", 19.99, '6"', 1.9, "power-rangers"],

  // Toy Biz Marvel Legends
  ["tb-wolverine-s1", "Wolverine", "Series 1 Brown Suit", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2002-06-01", 7.99, '6"', 8.5, "marvel,x-men,vintage"],
  ["tb-magneto-giant", "Magneto", "Giant-Size X-Men", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2005-03-01", 8.99, '6"', 6.2, "marvel,x-men,vintage"],
  ["tb-deadpool", "Deadpool", "Series 5", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2004-08-01", 8.99, '6"', 7.4, "marvel,vintage"],
  ["tb-sentinel-baf", "Sentinel", "Build-A-Figure", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2005-10-01", 54.0, '14"', 5.8, "marvel,x-men,vintage,baf"],
  ["tb-galactus", "Galactus", "18-inch", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2005-11-01", 39.99, '18"', 4.9, "marvel,vintage"],
  ["tb-apocalypse", "Apocalypse", "Series 4 BAF", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2005-06-01", 54.0, '9"', 4.2, "marvel,x-men,vintage,baf"],
  ["tb-punisher", "Punisher", "Series 3", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2003-11-01", 7.99, '6"', 5.1, "marvel,vintage"],
  ["tb-ghost-rider", "Ghost Rider", "Series 6", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2004-12-01", 8.99, '6"', 6.8, "marvel,vintage"],
  ["tb-blade", "Blade", "Vampire Hunter", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2004-04-01", 8.99, '6"', 4.6, "marvel,vintage"],
  ["tb-ironman", "Iron Man", "Modern Armor", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2006-02-01", 8.99, '6"', 3.9, "marvel,vintage"],
  ["tb-hulk", "Hulk", "Series 2", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2002-11-01", 12.99, '8"', 3.4, "marvel,vintage"],
  ["tb-spiderman", "Spider-Man", "Series 1", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2002-06-01", 7.99, '6"', 5.5, "marvel,spider-man,vintage"],
  ["tb-colossus", "Colossus", "Series 2", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2002-11-01", 7.99, '6"', 7.1, "marvel,x-men,vintage"],
  ["tb-onslaught", "Onslaught", "Deluxe", "Marvel Legends (Toy Biz)", "toybiz", "figure", "2006-08-01", 19.99, '10"', 3.2, "marvel,x-men,vintage"],

  // Mattel
  ["mv-heman", "He-Man", "Revelation", "Masters of the Universe Masterverse", "mattel", "figure", "2021-07-01", 22.99, '7"', 1.1, "motu"],
  ["mv-skeletor", "Skeletor", "Revelation", "Masters of the Universe Masterverse", "mattel", "figure", "2021-07-01", 22.99, '7"', 1.25, "motu"],
  ["mv-shera", "She-Ra", "Princess of Power", "Masters of the Universe Masterverse", "mattel", "figure", "2022-03-01", 22.99, '7"', 1.05, "motu"],
  ["mv-beastman", "Beast Man", "New Eternia", "Masters of the Universe Masterverse", "mattel", "figure", "2023-04-12", 24.99, '7"', 0.9, "motu"],
  ["mv-hordak", "Hordak", "New Eternia", "Masters of the Universe Masterverse", "mattel", "figure", "2023-09-01", 29.99, '7"', 1.35, "motu"],
  ["wwe-stone-cold", "Stone Cold Steve Austin", "Ultimate Edition", "WWE Elite", "mattel", "figure", "2022-01-15", 31.99, '6"', 1.4, "wwe"],
  ["wwe-rock", "The Rock", "Ultimate Edition", "WWE Elite", "mattel", "figure", "2021-08-01", 31.99, '6"', 1.5, "wwe"],
  ["wwe-taker", "The Undertaker", "Ministry", "WWE Elite", "mattel", "figure", "2023-03-01", 24.99, '6"', 1.2, "wwe"],
  ["wwe-hhogan", "Hulk Hogan", "Ultimate Edition", "WWE Elite", "mattel", "figure", "2023-07-20", 34.99, '6"', 1.15, "wwe"],
  ["dcuc-batman", "Batman", "Knightfall", "DC Universe Classics", "mattel", "figure", "2009-06-01", 12.99, '6"', 3.8, "dc,vintage"],
  ["dcuc-superman", "Superman", "Classic", "DC Universe Classics", "mattel", "figure", "2008-09-01", 12.99, '6"', 3.2, "dc,vintage"],
  ["dcuc-joker", "The Joker", "All-Star", "DC Universe Classics", "mattel", "figure", "2010-04-01", 12.99, '6"', 4.1, "dc,vintage"],
  ["hammond-t rex", "Tyrannosaurus Rex", "Hammond Collection", "Jurassic World", "mattel", "figure", "2021-06-01", 32.99, "7-inch", 1.6, "jurassic"],
  ["hammond-raptor", "Velociraptor", "Blue", "Jurassic World", "mattel", "figure", "2021-06-01", 19.99, '6"', 1.3, "jurassic"],

  // McFarlane
  ["mcf-batman-hush", "Batman", "Hush", "DC Multiverse", "mcfarlane", "figure", "2020-08-01", 19.99, '7"', 1.4, "dc"],
  ["mcf-superman-hush", "Superman", "Hush", "DC Multiverse", "mcfarlane", "figure", "2021-02-01", 19.99, '7"', 1.2, "dc"],
  ["mcf-flash", "The Flash", "Injustice 2", "DC Multiverse", "mcfarlane", "figure", "2021-07-01", 19.99, '7"', 0.85, "dc"],
  ["mcf-joker-tdkr", "The Joker", "The Dark Knight Returns", "DC Multiverse", "mcfarlane", "figure", "2022-03-01", 22.99, '7"', 1.35, "dc"],
  ["mcf-ww", "Wonder Woman", "Wonder Woman 1984", "DC Multiverse", "mcfarlane", "figure", "2020-12-01", 19.99, '7"', 0.7, "dc"],
  ["mcf-gl", "Green Lantern", "John Stewart", "DC Multiverse", "mcfarlane", "figure", "2022-08-01", 22.99, '7"', 1.05, "dc"],
  ["mcf-darkseid", "Darkseid", "Megafig", "DC Multiverse", "mcfarlane", "figure", "2022-11-01", 44.99, '10"', 1.5, "dc"],
  ["mcf-spawn-classic", "Spawn", "Classic", "Spawn", "mcfarlane", "figure", "2018-10-01", 24.99, '7"', 1.8, "spawn"],
  ["mcf-spawn-30", "Spawn", "30th Anniversary", "Spawn", "mcfarlane", "figure", "2022-05-01", 29.99, '7"', 1.45, "spawn"],
  ["mcf-violator", "Violator", "Megafig", "Spawn", "mcfarlane", "figure", "2021-09-01", 39.99, '9"', 1.25, "spawn"],
  ["mcf-batman-who-laughs", "The Batman Who Laughs", "Dark Nights", "DC Multiverse", "mcfarlane", "figure", "2020-02-01", 19.99, '7"', 2.2, "dc"],
  ["mcf-superman-page", "Superman", "Page Punchers", "DC Multiverse", "mcfarlane", "figure", "2022-06-01", 24.99, '7"', 0.95, "dc"],

  // MAFEX
  ["mf-superman-hush", "Superman", "Hush", "MAFEX", "mafex", "figure", "2018-08-01", 84.99, '6.5"', 2.4, "dc,import"],
  ["mf-batman-hush", "Batman", "Hush", "MAFEX", "mafex", "figure", "2018-12-01", 89.99, '6.5"', 2.6, "dc,import"],
  ["mf-joker-hush", "The Joker", "Hush", "MAFEX", "mafex", "figure", "2019-06-01", 89.99, '6.5"', 2.1, "dc,import"],
  ["mf-spiderman-comic", "Spider-Man", "Comic Ver. 2.0", "MAFEX", "mafex", "figure", "2021-04-01", 94.99, '6.5"', 1.9, "marvel,spider-man,import"],
  ["mf-ben-reilly", "Spider-Man", "Ben Reilly", "MAFEX", "mafex", "figure", "2022-09-01", 99.99, '6.5"', 2.3, "marvel,spider-man,import"],
  ["mf-wolverine-brown", "Wolverine", "Brown Suit", "MAFEX", "mafex", "figure", "2020-11-01", 94.99, '6.5"', 2.8, "marvel,x-men,import"],
  ["mf-ironman-comic", "Iron Man", "Comic Ver.", "MAFEX", "mafex", "figure", "2021-12-01", 109.99, '6.5"', 1.7, "marvel,import"],
  ["mf-cap", "Captain America", "Comic Ver.", "MAFEX", "mafex", "figure", "2022-03-01", 94.99, '6.5"', 1.5, "marvel,import"],
  ["mf-venom", "Venom", "Comic Ver.", "MAFEX", "mafex", "figure", "2023-05-01", 109.99, '6.5"', 2.0, "marvel,import"],
  ["mf-deadpool", "Deadpool", "X-Force", "MAFEX", "mafex", "figure", "2024-01-15", 104.99, '6.5"', 1.85, "marvel,import"],
  ["mf-knightfall-bats", "Batman", "Knightfall", "MAFEX", "mafex", "figure", "2023-08-01", 99.99, '6.5"', 1.65, "dc,import"],

  // Mezco One:12
  ["mz-batman-sk", "Batman", "Sovereign Knight", "One:12 Collective", "mezco", "figure", "2018-11-01", 80.0, '6.5"', 2.9, "dc,import"],
  ["mz-superman-recovery", "Superman", "Recovery Suit", "One:12 Collective", "mezco", "figure", "2020-09-01", 95.0, '6.5"', 2.2, "dc,import"],
  ["mz-spiderman", "Spider-Man", "Deluxe", "One:12 Collective", "mezco", "figure", "2019-05-01", 95.0, '6.5"', 1.8, "marvel,spider-man,import"],
  ["mz-punisher", "The Punisher", "Netflix", "One:12 Collective", "mezco", "figure", "2018-06-01", 80.0, '6.5"', 1.6, "marvel,import"],
  ["mz-doom", "Doctor Doom", "Classic", "One:12 Collective", "mezco", "figure", "2021-10-01", 125.0, '6.5"', 2.5, "marvel,import"],
  ["mz-hellboy", "Hellboy", "2019", "One:12 Collective", "mezco", "figure", "2019-09-01", 80.0, '6.5"', 1.7, "dark-horse,import"],
  ["mz-dredd", "Judge Dredd", "Pre-Order Classic", "One:12 Collective", "mezco", "figure", "2020-02-01", 95.0, '6.5"', 1.9, "2000ad,import"],
  ["mz-daredevil", "Daredevil", "Netflix", "One:12 Collective", "mezco", "figure", "2017-11-01", 75.0, '6.5"', 2.4, "marvel,import"],
  ["mz-ghost-rider", "Ghost Rider", "Marvel Knights", "One:12 Collective", "mezco", "figure", "2022-07-01", 115.0, '6.5"', 1.75, "marvel,import"],
  ["mz-rorschach", "Rorschach", "Watchmen", "One:12 Collective", "mezco", "figure", "2021-03-01", 95.0, '6.5"', 2.1, "dc,import"],
  ["mz-flash", "The Flash", "Deluxe", "One:12 Collective", "mezco", "figure", "2023-02-01", 115.0, '6.5"', 1.35, "dc,import"],

  // Bandai Gunpla
  ["gp-rg-rx78", "RX-78-2 Gundam", "Real Grade", "Gunpla", "bandai", "kit", "2010-07-01", 20.0, "1/144", 1.4, "gundam,kit"],
  ["gp-rg-sazabi", "Sazabi", "Real Grade", "Gunpla", "bandai", "kit", "2018-08-01", 50.0, "1/144", 1.8, "gundam,kit"],
  ["gp-rg-wing-zero", "Wing Gundam Zero EW", "Real Grade", "Gunpla", "bandai", "kit", "2020-07-01", 40.0, "1/144", 1.55, "gundam,kit"],
  ["gp-rg-god", "God Gundam", "Real Grade", "Gunpla", "bandai", "kit", "2022-08-01", 40.0, "1/144", 1.35, "gundam,kit"],
  ["gp-mg-unicorn", "Unicorn Gundam", "Master Grade", "Gunpla", "bandai", "kit", "2010-12-01", 56.0, "1/100", 1.7, "gundam,kit"],
  ["gp-mg-zaku", "MS-06S Zaku II", "Master Grade 2.0", "Gunpla", "bandai", "kit", "2007-04-01", 32.0, "1/100", 1.5, "gundam,kit"],
  ["gp-mg-exia", "Gundam Exia", "Master Grade", "Gunpla", "bandai", "kit", "2008-07-01", 45.0, "1/100", 1.6, "gundam,kit"],
  ["gp-hg-aerial", "Gundam Aerial", "High Grade", "Gunpla", "bandai", "kit", "2022-10-01", 22.0, "1/144", 1.25, "gundam,kit"],
  ["gp-eg-rx78", "RX-78-2 Gundam", "Entry Grade", "Gunpla", "bandai", "kit", "2020-08-01", 10.0, "1/144", 0.9, "gundam,kit"],
  ["gp-pg-strike", "Strike Freedom Gundam", "Perfect Grade", "Gunpla", "bandai", "kit", "2016-12-01", 220.0, "1/60", 1.45, "gundam,kit"],
  ["gp-mg-barbatos", "Gundam Barbatos", "Master Grade", "Gunpla", "bandai", "kit", "2016-09-01", 45.0, "1/100", 1.3, "gundam,kit"],
  ["gp-rg-hi-nu", "Hi-Nu Gundam", "Real Grade", "Gunpla", "bandai", "kit", "2021-06-01", 48.0, "1/144", 1.65, "gundam,kit"],

  // SH Figuarts
  ["shf-goku-ss", "Son Goku", "Super Saiyan", "S.H.Figuarts", "shfiguarts", "figure", "2018-06-01", 54.99, '6"', 1.8, "dbz,anime"],
  ["shf-vegeta", "Vegeta", "Super Saiyan", "S.H.Figuarts", "shfiguarts", "figure", "2019-03-01", 59.99, '6"', 1.55, "dbz,anime"],
  ["shf-goku-ui", "Son Goku", "Ultra Instinct", "S.H.Figuarts", "shfiguarts", "figure", "2020-11-01", 74.99, '6"', 2.2, "dbz,anime"],
  ["shf-ironman-mk6", "Iron Man", "Mark VI", "S.H.Figuarts", "shfiguarts", "figure", "2019-08-01", 84.99, '6"', 1.7, "marvel"],
  ["shf-spiderman-nwh", "Spider-Man", "No Way Home", "S.H.Figuarts", "shfiguarts", "figure", "2022-05-01", 79.99, '6"', 1.6, "marvel,spider-man"],
  ["shf-naruto", "Naruto Uzumaki", "Sage Mode", "S.H.Figuarts", "shfiguarts", "figure", "2021-07-01", 64.99, '6"', 1.45, "anime"],
  ["shf-luffy-g5", "Monkey D. Luffy", "Gear 5", "S.H.Figuarts", "shfiguarts", "figure", "2023-11-01", 89.99, '6"', 2.4, "anime,one-piece"],
  ["shf-vader", "Darth Vader", "Star Wars", "S.H.Figuarts", "shfiguarts", "figure", "2016-09-01", 64.99, '6"', 1.9, "star-wars"],
  ["shf-luke", "Luke Skywalker", "A New Hope", "S.H.Figuarts", "shfiguarts", "figure", "2017-04-01", 59.99, '6"', 1.35, "star-wars"],
  ["shf-gojo", "Satoru Gojo", "Jujutsu Kaisen", "S.H.Figuarts", "shfiguarts", "figure", "2022-12-01", 74.99, '6"', 2.1, "anime"],
  ["shf-chainsaw", "Denji", "Chainsaw Man", "S.H.Figuarts", "shfiguarts", "figure", "2023-06-01", 79.99, '6"', 1.7, "anime"],
  ["shf-ichigo", "Ichigo Kurosaki", "Bankai", "S.H.Figuarts", "shfiguarts", "figure", "2021-02-01", 69.99, '6"', 1.5, "anime"],

  // NECA
  ["neca-leo-90", "Leonardo", "1990 Movie", "TMNT", "neca", "figure", "2020-04-01", 32.99, '7"', 1.6, "tmnt"],
  ["neca-ralph-90", "Raphael", "1990 Movie", "TMNT", "neca", "figure", "2020-04-01", 32.99, '7"', 1.5, "tmnt"],
  ["neca-don-90", "Donatello", "1990 Movie", "TMNT", "neca", "figure", "2020-07-01", 32.99, '7"', 1.45, "tmnt"],
  ["neca-mikey-90", "Michelangelo", "1990 Movie", "TMNT", "neca", "figure", "2020-07-01", 32.99, '7"', 1.55, "tmnt"],
  ["neca-alien", "Xenomorph", "Big Chap", "Aliens", "neca", "figure", "2017-05-01", 34.99, '8"', 1.8, "horror"],
  ["neca-predator", "Jungle Hunter", "Predator 1987", "Predator", "neca", "figure", "2016-08-01", 34.99, '8"', 2.0, "horror"],
  ["neca-ash", "Ash Williams", "Evil Dead 2", "Evil Dead", "neca", "figure", "2018-10-01", 32.99, '7"', 1.7, "horror"],
  ["neca-frank", "Frankenstein", "Universal Monsters", "Universal Monsters", "neca", "figure", "2021-09-01", 34.99, '7"', 1.4, "horror"],
  ["neca-godzilla", "Godzilla", "2001", "Godzilla", "neca", "figure", "2019-06-01", 64.99, '12"', 1.65, "kaiju"],
  ["neca-gizmo", "Gizmo", "Gremlins", "Gremlins", "neca", "figure", "2020-11-01", 29.99, '4"', 1.3, "horror"],

  // Super7
  ["s7-heman", "He-Man", "ULTIMATES", "Super7 ULTIMATES", "super7", "figure", "2020-10-01", 55.0, '7"', 1.35, "motu"],
  ["s7-skeletor", "Skeletor", "ULTIMATES", "Super7 ULTIMATES", "super7", "figure", "2020-10-01", 55.0, '7"', 1.5, "motu"],
  ["s7-lion-o", "Lion-O", "ThunderCats", "Super7 ULTIMATES", "super7", "figure", "2021-06-01", 55.0, '7"', 1.55, "thundercats"],
  ["s7-tmnt-leo", "Leonardo", "Mirage", "Super7 ULTIMATES", "super7", "figure", "2021-03-01", 55.0, '7"', 1.25, "tmnt"],
  ["s7-silverhawks", "Quicksilver", "SilverHawks", "Super7 ULTIMATES", "super7", "figure", "2022-08-01", 55.0, '7"', 1.1, "silverhawks"],
  ["s7-mmpr-red", "Red Ranger", "Mighty Morphin", "Super7 ULTIMATES", "super7", "figure", "2022-04-01", 55.0, '7"', 1.4, "power-rangers"],
  ["s7-reaction-vader", "Darth Vader", "ReAction", "Super7 ReAction", "super7", "figure", "2019-05-01", 18.0, '3.75"', 1.2, "star-wars"],

  // Hot Toys
  ["ht-ironman-85", "Iron Man", "Mark LXXXV", "Movie Masterpiece", "hottoys", "figure", "2020-04-01", 380.0, "1/6", 1.35, "marvel,sixth-scale"],
  ["ht-batman-tdk", "Batman", "The Dark Knight", "Movie Masterpiece", "hottoys", "figure", "2019-07-01", 350.0, "1/6", 1.7, "dc,sixth-scale"],
  ["ht-joker-tdk", "The Joker", "The Dark Knight", "Movie Masterpiece", "hottoys", "figure", "2018-11-01", 350.0, "1/6", 2.4, "dc,sixth-scale"],
  ["ht-spiderman-nwh", "Spider-Man", "No Way Home", "Movie Masterpiece", "hottoys", "figure", "2022-12-01", 310.0, "1/6", 1.25, "marvel,spider-man,sixth-scale"],
  ["ht-mando", "The Mandalorian", "Beskar", "Movie Masterpiece", "hottoys", "figure", "2021-05-01", 320.0, "1/6", 1.3, "star-wars,sixth-scale"],
  ["ht-deadpool", "Deadpool", "Deadpool 2", "Movie Masterpiece", "hottoys", "figure", "2019-03-01", 310.0, "1/6", 1.55, "marvel,sixth-scale"],

  // Figma
  ["fg-link-botw", "Link", "Breath of the Wild", "Figma", "figma", "figure", "2017-03-01", 79.99, '6"', 2.1, "nintendo,zelda"],
  ["fg-cloud", "Cloud Strife", "Final Fantasy VII", "Figma", "figma", "figure", "2020-04-01", 89.99, '6"', 1.8, "final-fantasy"],
  ["fg-spiderman", "Spider-Man", "Amazing Yamaguchi-adj", "Figma", "figma", "figure", "2016-08-01", 64.99, '6"', 1.9, "marvel,spider-man"],
  ["fg-samus", "Samus Aran", "Prime 3", "Figma", "figma", "figure", "2017-09-01", 74.99, '6"', 2.3, "nintendo,metroid"],
  ["fg-2b", "2B", "NieR:Automata", "Figma", "figma", "figure", "2018-05-01", 84.99, '6"', 2.0, "nier"],

  // Kotobukiya
  ["koto-batman-artfx", "Batman", "ARTFX+ Hush", "ARTFX+", "kotobukiya", "figure", "2019-06-01", 89.99, "1/10", 1.4, "dc,statue"],
  ["koto-vader-artfx", "Darth Vader", "Industrial Empire", "ARTFX", "kotobukiya", "kit", "2018-02-01", 64.99, "1/7", 1.55, "star-wars,kit"],
  ["koto-harley-bishoujo", "Harley Quinn", "Bishoujo", "Bishoujo", "kotobukiya", "figure", "2017-11-01", 54.99, "1/7", 1.7, "dc,statue"],
  ["koto-eva-01", "EVA-01", "Test Type", "Evangelion Model", "kotobukiya", "kit", "2015-06-01", 54.99, "1/400", 1.6, "evangelion,kit"],
  ["koto-ironman-fine", "Iron Man", "Fine Art Statue", "Fine Art", "kotobukiya", "figure", "2020-09-01", 199.99, "1/6", 1.25, "marvel,statue"],

  // Storm
  ["st-scorpion", "Scorpion", "Mortal Kombat", "Storm Collectibles", "storm", "figure", "2017-08-01", 89.99, '1/12', 2.2, "mk"],
  ["st-subzero", "Sub-Zero", "Mortal Kombat", "Storm Collectibles", "storm", "figure", "2017-08-01", 89.99, '1/12', 2.0, "mk"],
  ["st-ryu", "Ryu", "Street Fighter", "Storm Collectibles", "storm", "figure", "2016-05-01", 79.99, '1/12', 1.85, "sf"],
  ["st-terry", "Terry Bogard", "Fatal Fury", "Storm Collectibles", "storm", "figure", "2019-03-01", 89.99, '1/12', 1.6, "fatal-fury"],
  ["st-akuma", "Akuma", "Street Fighter", "Storm Collectibles", "storm", "figure", "2018-01-01", 89.99, '1/12', 1.9, "sf"],

  // Extra checklist depth
  ["ml-beast-97", "Beast", "X-Men '97", "Marvel Legends", "hasbro", "figure", "2025-03-01", 24.99, '6"', 1.3, "marvel,x-men"],
  ["ml-jubilee-97", "Jubilee", "X-Men '97", "Marvel Legends", "hasbro", "figure", "2025-03-01", 24.99, '6"', 1.25, "marvel,x-men"],
  ["ml-secret-wars-cap", "Captain America", "Secret Wars", "Marvel Legends", "hasbro", "figure", "2024-05-18", 24.99, '6"', 1.4, "marvel"],
  ["ml-haslab-galactus", "Galactus", "HasLab", "Marvel Legends", "hasbro", "figure", "2022-12-01", 399.99, '32"', 1.9, "marvel", { exclusive: "Hasbro Pulse" }],
  ["bs-luke-farmboy", "Luke Skywalker", "A New Hope", "Star Wars Black Series", "hasbro", "figure", "2016-09-01", 19.99, '6"', 1.8, "star-wars"],
  ["bs-palpatine", "Emperor Palpatine", "Return of the Jedi", "Star Wars Black Series", "hasbro", "figure", "2020-10-01", 22.99, '6"', 1.35, "star-wars"],
  ["bs-cal-kestis", "Cal Kestis", "Jedi Survivor", "Star Wars Black Series", "hasbro", "figure", "2023-04-01", 24.99, '6"', 1.15, "star-wars"],
  ["joe-baroness", "Baroness", "Cobra Intelligence", "GI Joe Classified", "hasbro", "figure", "2021-06-01", 22.99, '6"', 1.45, "gi-joe"],
  ["ss-starscream", "Starscream", "Bumblebee Movie", "Transformers Studio Series", "hasbro", "figure", "2019-11-01", 29.99, "Deluxe", 1.5, "transformers"],
  ["mcf-the-batman", "Batman", "The Batman 2022", "DC Multiverse", "mcfarlane", "figure", "2022-04-01", 19.99, '7"', 1.3, "dc"],
  ["mcf-supergirl", "Supergirl", "Rebirth", "DC Multiverse", "mcfarlane", "figure", "2023-06-01", 22.99, '7"', 0.95, "dc"],
  ["mf-hush-bats-20", "Batman", "Hush 2.0", "MAFEX", "mafex", "figure", "2024-06-01", 109.99, '6.5"', 2.2, "dc,import"],
  ["mz-moon-knight", "Moon Knight", "Marvel Knights", "One:12 Collective", "mezco", "figure", "2023-09-01", 115.0, '6.5"', 1.85, "marvel,import"],
  ["shf-goku-ssb", "Son Goku", "Super Saiyan Blue", "S.H.Figuarts", "shfiguarts", "figure", "2021-11-01", 64.99, '6"', 1.75, "dbz,anime"],
  ["shf-vegeta-ssb", "Vegeta", "Super Saiyan Blue", "S.H.Figuarts", "shfiguarts", "figure", "2022-02-01", 64.99, '6"', 1.6, "dbz,anime"],
  ["neca-casey", "Casey Jones", "1990 Movie", "TMNT", "neca", "figure", "2021-03-01", 32.99, '7"', 1.55, "tmnt"],
  ["ht-ironman-mk3", "Iron Man", "Mark III", "Movie Masterpiece", "hottoys", "figure", "2018-05-01", 340.0, "1/6", 1.9, "marvel,sixth-scale"],
  ["gp-pg-unicorn", "Unicorn Gundam", "Perfect Grade", "Gunpla", "bandai", "kit", "2014-12-01", 230.0, "1/60", 1.7, "gundam,kit"],
  ["gp-rg-nu", "Nu Gundam", "Real Grade", "Gunpla", "bandai", "kit", "2019-08-01", 50.0, "1/144", 1.75, "gundam,kit"],
];

export const FIGURES: CatalogFigure[] = rows.map(
  ([id, name, subtitle, line, company, kind, releaseDate, msrp, scale, demand, tags, extra]) => ({
    id,
    name,
    subtitle,
    line,
    company,
    kind,
    releaseDate,
    msrp,
    scale,
    demand,
    tags: tags.split(","),
    sku: extra?.sku,
    exclusive: extra?.exclusive,
  }),
);

export const FIGURE_BY_ID: Record<string, CatalogFigure> = Object.fromEntries(
  FIGURES.map((f) => [f.id, f]),
);

export const LINES_BY_COMPANY: Record<CompanyId, string[]> = FIGURES.reduce(
  (acc, f) => {
    const list = acc[f.company] ?? [];
    if (!list.includes(f.line)) list.push(f.line);
    acc[f.company] = list;
    return acc;
  },
  {} as Record<CompanyId, string[]>,
);

function figureKey(f: { name: string; subtitle: string; line: string; company: string }) {
  return `${f.name}|${f.subtitle}|${f.line}|${f.company}`.toLowerCase();
}

export function mergeFigures(extras: CatalogFigure[] = []): CatalogFigure[] {
  if (!extras.length) return FIGURES;
  const seen = new Set(FIGURES.map(figureKey));
  const add = extras.filter((f) => !seen.has(figureKey(f)));
  return add.length ? [...FIGURES, ...add] : FIGURES;
}

export function figureById(id: string, extras: CatalogFigure[] = []): CatalogFigure | undefined {
  return FIGURE_BY_ID[id] ?? extras.find((f) => f.id === id);
}

export function searchFigures(query: string, extras: CatalogFigure[] = []): CatalogFigure[] {
  const list = mergeFigures(extras);
  const q = query.trim().toLowerCase();
  if (!q) return list;
  return list.filter((f) => {
    const hay = `${f.name} ${f.subtitle} ${f.line} ${f.company} ${f.sku ?? ""} ${f.exclusive ?? ""} ${f.tags.join(" ")}`.toLowerCase();
    return hay.includes(q);
  });
}
