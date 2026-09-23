import { defineCollection, z } from "astro:content";

const events = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    eventId: z.string(),
    date: z.string(),
    start: z.string().optional(),
    end: z.string().optional(),
    sort: z.number(),
    place: z.string().optional(),
    themes: z.array(z.string()).default([]),
    themeKeys: z.array(z.string()).default([]),
    page: z.string(),
    image: z.string().optional(),
    images: z.array(z.string()).default([]),
    fbid: z.string().optional(),
    hasDetail: z.boolean().default(true)
  })
});

const notes = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    date: z.string().optional(),
    sort: z.number().optional(),
    kind: z.string().optional(),
    image: z.string().optional()
  })
});

const external = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    date: z.string(),
    displayDate: z.string(),
    sort: z.number(),
    category: z.string(),
    confidence: z.string(),
    sourceLabel: z.string(),
    sourceUrl: z.string().optional(),
    sourceUrls: z.array(z.string()).default([])
  })
});

const pages = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string().optional()
  })
});

const reports = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    sourcePath: z.string().optional()
  })
});

const slides = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    image: z.string(),
    alt: z.string().optional(),
    sort: z.number().default(0)
  })
});

export const collections = { events, external, notes, pages, reports, slides };
