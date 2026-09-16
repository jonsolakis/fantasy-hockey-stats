<script>
  const releases = [
    {
      date: 'September 16, 2026',
      title: 'Position filters',
      changes: [
        'Filter rankings by every position available in the imported NHL data.',
        'Position filters update the player table, pagination, movers, and top-player breakdown together.'
      ]
    },
    {
      date: 'September 10, 2026',
      title: 'More reliable imports',
      changes: [
        'Moved application storage to PostgreSQL.',
        'Season imports now run separately from the API, so an NHL API outage does not take the site offline.'
      ]
    }
  ];
</script>

<svelte:head>
  <title>What’s changed · Fantasy Hockey Stats</title>
  <meta name="description" content="Recent updates to Fantasy Hockey Stats." />
</svelte:head>

<main>
  <a class="back-link" href="/">← Back to rankings</a>
  <section class="intro">
    <p>What’s changed</p>
    <h1>Recent updates</h1>
    <span>New features and reliability improvements for Fantasy Hockey Stats.</span>
  </section>

  <section class="releases" aria-label="Changelog">
    {#each releases as release}
      <article>
        <time>{release.date}</time>
        <h2>{release.title}</h2>
        <ul>
          {#each release.changes as change}
            <li>{change}</li>
          {/each}
        </ul>
      </article>
    {/each}
  </section>
</main>

<style>
  :global(*) { box-sizing: border-box; }
  :global(body) { margin: 0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #e8f0fb; background: #07111e; }
  main { width: min(760px, 100%); min-height: 100vh; margin: 0 auto; padding: 3rem clamp(1.25rem, 4vw, 3rem); }
  .back-link { color: #83dafa; font-size: .9rem; text-decoration: none; }
  .back-link:hover, .back-link:focus-visible { color: #eafbff; text-decoration: underline; }
  .intro { margin: 3rem 0 2rem; }
  .intro p { margin: 0; color: #63d6ff; font-size: .75rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
  h1 { margin: .35rem 0 .7rem; font-size: clamp(2rem, 5vw, 3rem); letter-spacing: -.04em; }
  .intro span { color: #9db2ca; line-height: 1.5; }
  .releases { display: grid; gap: 1rem; }
  article { padding: 1.5rem; border: 1px solid #1d354e; border-radius: .8rem; background: #0d1a2a; }
  time { color: #86a0ba; font-size: .8rem; font-weight: 650; }
  h2 { margin: .4rem 0 .85rem; font-size: 1.25rem; }
  ul { display: grid; gap: .55rem; margin: 0; padding-left: 1.2rem; color: #b8cadd; line-height: 1.5; }
</style>
