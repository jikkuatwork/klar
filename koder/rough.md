# Silversky

## Overview

I would like to build a web app to visualise data.csv

My ideas:
vanila/ no build
takes in data.csv itself as source data ; and perhaps transforms to JSON or similar for frontend
has multiple tabs: dashboard (vital stats), list (with filters), map, histogram (indsutry/geography/financials/etc), saved lists, chat
ability to export filtered lists
ability to save filtered/selected list to save list with a custom label
a chat system that has a tool, that is aware of the data structure and can do filters based on natural language query
add data, so that it can be saved to the primary list; (will save to local storage)
can handle null fields; will gracefully handle than errors
data will be stored in local storage so that it won't have to loaded each time
super speed (should we use index db?)
use JS libraries to place the people/funds in map? and show flags?
zero jank, pwa, with responsive layout, use nice icons, use inter font
page doesn't scroll only internal panels scroll, giving a native feel
this is fully static, hosted un Vercel
Evaluate whether this is buildable?
fully by an LLM
are the features possible without React?
Would like to give them a nice, native feel.

---

- koder is a meta folder
- have separate phases
- assume data.csv will be available in root
- split each phase into granular todos
- add which libraries to use
- implement a settings tab too
- aesthetics:
   - super minimal / elegant
   - implement light / dark mode
   - use tailwind cdn
   - use theme colors (primary: DEC26F ; secondary: 15213B)
   - build components when possible
   - use nice animations
   - avoid layout janks
   - make it look like a native app; avoid page level scrolls, make make panels inside the view port scroll
   - use the city/country codes for geo mapping and flags, use proper libraries for that
   - use feather icons
- build the frontend into frontend/01/ (as I will use multiple LLMs to build different frontends; we will symlink data.csv into the folder)
- Assume, we will use vercel ai npm package's compilled version in page; and use Gemini 2.5 pro to do it (just mock the chat tab for now)|


## Requirement

- evaluate the requirement/context
- suggest more/better visualisation ideas
- Do you have confidence to build a detailed plan in koder/plans/? or do you
  have questions before doing it?

## Plan

- split into phases
- split phases into granular todos
- reference libraries to use
- mark todos after completion
- commit after phases
