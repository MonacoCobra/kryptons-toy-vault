declare module "virtual:grok-og-identity" {
  export const grokOgIdentity: {
    site: {
      title?: string;
      shortName?: string;
      description?: string;
      type?: string;
      card?: string;
      image?: string;
      banner?: string;
      color?: string;
      themeColor?: string;
      backgroundColor?: string;
      icons?: Array<{
        src: string;
        sizes: string;
        type: string;
        purpose?: string;
      }>;
    };
  };
}
