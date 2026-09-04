export type CompanyId =
  | "hasbro"
  | "toybiz"
  | "mattel"
  | "mcfarlane"
  | "mafex"
  | "mezco"
  | "bandai"
  | "shfiguarts"
  | "neca"
  | "super7"
  | "hottoys"
  | "figma"
  | "kotobukiya"
  | "storm";

export type ItemKind = "figure" | "kit";

export type Condition = "mib" | "opened" | "loose";

export type ComicFormat = "single" | "annual" | "tpb" | "hc" | "omnibus" | "facsimile";

export type ComicGrade =
  | "raw"
  | "10.0"
  | "9.8"
  | "9.6"
  | "9.4"
  | "9.2"
  | "9.0"
  | "8.5"
  | "8.0"
  | "7.5"
  | "7.0"
  | "6.0"
  | "5.0"
  | "4.0"
  | "3.0"
  | "2.0"
  | "1.0";

export type Company = {
  id: CompanyId;
  name: string;
  short: string;
  blurb: string;
  founded: string;
  hq: string;
  accent: string;
};

export type CatalogFigure = {
  id: string;
  name: string;
  subtitle: string;
  line: string;
  company: CompanyId;
  kind: ItemKind;
  releaseDate: string;
  msrp: number;
  scale: string;
  sku?: string;
  exclusive?: string;
  demand: number;
  tags: string[];
};

export type SoldComp = {
  price: number;
  date: string;
  condition: string;
  title: string;
  /** Sold listing URL when sourced from eBay. */
  url?: string;
  source?: "ebay" | "synthetic";
};

export type OwnedFigure = {
  figureId: string;
  acquiredDate?: string;
  acquiredPrice?: number;
  condition: Condition;
  photoDataUrl?: string;
  notes?: string;
  addedAt: string;
};

export type CatalogComic = {
  id: string;
  series: string;
  issue: string;
  publisher: string;
  coverDate: string;
  streetDate?: string;
  writers: string[];
  artists: string[];
  description: string;
  msrp: number;
  format: ComicFormat;
  variant?: string;
  upc?: string;
  demand: number;
  key?: boolean;
  palette: [string, string, string];
  cover?: string;
};

export type CustomComic = {
  id: string;
  series: string;
  issue: string;
  publisher: string;
  coverDate?: string;
  writers?: string[];
  artists?: string[];
  description?: string;
  msrp?: number;
  format: ComicFormat;
  variant?: string;
  upc?: string;
};

export type OwnedComic = {
  id: string;
  catalogId?: string;
  custom?: CustomComic;
  acquiredDate?: string;
  acquiredPrice?: number;
  grade: ComicGrade;
  photoDataUrl?: string;
  notes?: string;
  addedAt: string;
};

export type WishlistItem = {
  id: string;
  addedAt: string;
};

export type VaultState = {
  ownedFigures: Record<string, OwnedFigure>;
  wantedFigures: Record<string, WishlistItem>;
  ownedComics: Record<string, OwnedComic>;
  wantedComics: Record<string, WishlistItem>;
  customComics: Record<string, CustomComic>;
};

export type WeeklyDrop = {
  week: string;
  fetchedAt: string;
  comics: CatalogComic[];
  figures: CatalogFigure[];
  status: "ok" | "error";
  error?: string;
};
