import adapter from '@sveltejs/adapter-static'
import { s } from 'hastscript'
import { mdsvex } from 'mdsvex'
import link_headings from 'rehype-autolink-headings'
import katex from 'rehype-katex-svelte'
import heading_slugs from 'rehype-slug'
import math from 'remark-math'
import preprocess from 'svelte-preprocess'

const { default: pkg } = await import(`./package.json`, {
  assert: { type: `json` },
})

/** @type {import('@sveltejs/kit').Config} */
export default {
  extensions: [`.svelte`, `.svx`, `.md`],

  preprocess: [
    // replace readme links to docs with site-internal links
    // (which don't require browser navigation)
    preprocess({ replace: [[pkg.homepage, ``]] }),
    mdsvex({
      rehypePlugins: [
        katex,
        heading_slugs,
        [
          link_headings,
          {
            behavior: `append`,
            test: [`h2`, `h3`, `h4`, `h5`, `h6`], // don't auto-link <h1>
            content: s(
              `svg`,
              { width: 16, height: 16, viewBox: `0 0 16 16` },
              // symbol #octicon-link defined in app.html
              s(`use`, { 'xlink:href': `#octicon-link` })
            ),
          },
        ],
      ],
      // remark-math@3.0.0 pinned due to mdsvex, see
      // https://github.com/kwshi/rehype-katex-svelte#usage
      remarkPlugins: [math],
      extensions: [`.svx`, `.md`],
    }),
    {
      markup: (file) => {
        const route = file.filename.split(`site/src/routes/`)[1]?.split(`/`)[0]
        if (!route) return

        if (route.startsWith(`paper`) || route.startsWith(`si`)) {
          let fig_index = new Set()
          let ref_index = new Set()

          // Replace figure labels with 'Fig. {n}' and add to fig_index
          let code = file.content.replace(
            /@label:(fig:[^\s]+)/g,
            (_match, id) => {
              fig_index.add(id)
              const idx = (route.startsWith(`si`) ? `S` : ``) + fig_index.size
              const link_icon = `<a aria-hidden="true" tabindex="-1" href="#${id}"><svg width="16" height="16" viewBox="0 0 16 16"><use xlink:href="#octicon-link"></use></svg></a>`
              return `<strong id='${id}'>${link_icon}Fig. ${idx}</strong>`
            }
          )

          // Replace figure references with 'Fig. {n}' and add to fig_index
          code = code.replace(/@(fig[^\s]+)/g, (_full_str, id) => {
            let idx = [...fig_index].indexOf(`fig${id}`) + 1
            if (idx == 0) {
              console.error(`Figure id ${id} not found`)
              idx = `not found`
            }
            return `<a href="#${id}">Fig. ${idx}</a>`
          })

          // preprocess markdown citations @auth_1st-word-title_yyyy into superscript
          // links to bibliography items, href must match id format in References.svelte
          code = code.replace(
            /@((.+?)_.+?_(\d{4}))/g,
            (_match, id, author, year) => {
              ref_index.add(id)

              const idx = [...ref_index].indexOf(id)
              if (idx == -1) {
                console.error(`Reference id ${id} not found`)
              }
              return `<sup class="ref"><a href="#${id}">${author} ${year}</a></sup>`
            }
          )

          return { code }
        }
      },
    },
  ],

  kit: {
    adapter: adapter(),

    alias: {
      $site: `.`,
      $root: `..`,
      $paper: `src/routes/paper`,
      $figs: `src/figs`,
    },
  },
}
