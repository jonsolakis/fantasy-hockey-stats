<script>
  import { onMount } from 'svelte';

  let seasons = [];
  let profiles = [];
  let baselineRankings = [];
  let customRankings = [];
  let selectedSeason = '';
  let selectedProfile = '';
  let playerType = 'all';
  let positionFilter = 'all';
  let draftRules = [];
  let pageSize = 25;
  let reportSize = 50;
  let reportsCollapsed = false;
  let editorCollapsed = false;
  let reportsWidth = 240;
  let editorWidth = 310;
  let workspaceElement;
  let showProfiles = false;
  let showSaveProfile = false;
  let newProfileName = '';
  let savingProfile = false;
  let profileError = '';
  let page = 1;
  let loading = true;
  let error = '';

  onMount(async () => {
    try {
      const [seasonResponse, profileResponse] = await Promise.all([
        fetch('/api/seasons'),
        fetch('/api/scoring-profiles')
      ]);
      if (!seasonResponse.ok || !profileResponse.ok) throw new Error('Could not load hockey data.');

      seasons = await seasonResponse.json();
      profiles = await profileResponse.json();
      selectedSeason = seasons[0]?.season_id ?? '';
      selectedProfile = String(defaultProfile()?.id ?? '');
      setProfileRules();
      await loadRankings();
    } catch (cause) {
      error = cause.message;
    } finally {
      loading = false;
    }
  });

  async function loadRankings() {
    if (!selectedSeason || !selectedProfile) {
      baselineRankings = [];
      customRankings = [];
      return;
    }

    const [baselineResponse, customResponse] = await Promise.all([
      fetch(`/api/rankings?season_id=${selectedSeason}&profile_id=${selectedProfile}&player_type=${playerType}`),
      fetch('/api/rankings/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ season_id: Number(selectedSeason), player_type: playerType, rules: draftRules })
      })
    ]);
    if (!baselineResponse.ok || !customResponse.ok) throw new Error('Could not calculate rankings.');
    baselineRankings = await baselineResponse.json();
    customRankings = await customResponse.json();
    if (positionFilter !== 'all' && !availablePositions().includes(positionFilter)) {
      positionFilter = 'all';
    }
    page = 1;
  }

  async function updateRankings() {
    loading = true;
    error = '';
    try {
      await loadRankings();
    } catch (cause) {
      error = cause.message;
    } finally {
      loading = false;
    }
  }

  function setProfileRules() {
    const profile = profiles.find((item) => item.id === Number(selectedProfile));
    const pointsByStat = new Map((profile?.rules ?? []).map((rule) => [rule.stat_key, rule.points]));
    draftRules = activeStatCategories().map((category) => ({
      stat_key: category.key,
      points: pointsByStat.get(category.key) ?? 0
    }));
  }

  function pointsFor(statKey) {
    return draftRules.find((rule) => rule.stat_key === statKey)?.points ?? 0;
  }

  function updatePoints(statKey, value) {
    const points = Number(value);
    draftRules = draftRules.map((rule) =>
      rule.stat_key === statKey ? { ...rule, points: Number.isFinite(points) ? points : 0 } : rule
    );
  }

  async function resetProfile() {
    setProfileRules();
    await updateRankings();
  }

  function currentProfileName() {
    return profiles.find((profile) => profile.id === Number(selectedProfile))?.name ?? 'Yahoo Default';
  }

  async function chooseProfile(profileId) {
    selectedProfile = String(profileId);
    setProfileRules();
    showProfiles = false;
    await updateRankings();
  }

  async function saveProfile() {
    const name = newProfileName.trim();
    if (!name) {
      profileError = 'Enter a profile name.';
      return;
    }
    savingProfile = true;
    profileError = '';
    try {
      const response = await fetch('/api/scoring-profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, rules: draftRules })
      });
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.detail ?? 'Could not save profile.');
      }
      const created = await response.json();
      const profilesResponse = await fetch('/api/scoring-profiles');
      if (!profilesResponse.ok) throw new Error('Profile saved, but the profile list could not be refreshed.');
      profiles = await profilesResponse.json();
      selectedProfile = String(created.id);
      newProfileName = '';
      showSaveProfile = false;
      await updateRankings();
    } catch (cause) {
      profileError = cause.message;
    } finally {
      savingProfile = false;
    }
  }

  async function selectPlayerType(nextPlayerType) {
    playerType = nextPlayerType;
    positionFilter = 'all';
    selectedProfile = String(defaultProfile()?.id ?? '');
    setProfileRules();
    await updateRankings();
  }

  function seasonLabel(seasonId) {
    const value = String(seasonId);
    return `${value.slice(0, 4)}–${value.slice(4)}`;
  }

  function comparisonRows() {
    const baselineByPlayer = new Map(baselineRankings.map((player) => [player.player_id, player]));
    return customRankings.map((custom) => {
      const baseline = baselineByPlayer.get(custom.player_id);
      return {
        ...custom,
        baseline_rank: baseline?.rank ?? null,
        baseline_points: baseline?.fantasy_points ?? 0,
        rank_change: baseline ? baseline.rank - custom.rank : 0
      };
    });
  }

  function filteredComparisonRows() {
    return comparisonRows().filter((player) => positionFilter === 'all' || player.position === positionFilter);
  }

  function filteredCustomRankings() {
    return customRankings.filter((player) => positionFilter === 'all' || player.position === positionFilter);
  }

  function availablePositions() {
    const preferredOrder = ['C', 'LW', 'RW', 'L', 'R', 'D', 'G'];
    const positions = new Set(customRankings.map((player) => player.position).filter(Boolean));
    return [...positions].sort((left, right) => {
      const leftIndex = preferredOrder.indexOf(left);
      const rightIndex = preferredOrder.indexOf(right);
      return (leftIndex === -1 ? preferredOrder.length : leftIndex) - (rightIndex === -1 ? preferredOrder.length : rightIndex)
        || left.localeCompare(right);
    });
  }

  function positionLabel(position) {
    return { L: 'LW', R: 'RW' }[position] ?? position;
  }

  function selectPosition(nextPosition) {
    positionFilter = nextPosition;
    page = 1;
  }

  function movers(direction) {
    return filteredComparisonRows()
      .filter((player) => (direction === 'up' ? player.rank_change > 0 : player.rank_change < 0))
      .sort((left, right) => direction === 'up' ? right.rank_change - left.rank_change : left.rank_change - right.rank_change)
      .slice(0, 5);
  }

  function totalPages() {
    return Math.max(1, Math.ceil(filteredComparisonRows().length / pageSize));
  }

  function pageRows() {
    const start = (page - 1) * pageSize;
    return filteredComparisonRows().slice(start, start + pageSize);
  }

  function setPageSize() {
    page = 1;
  }

  function changePage(nextPage) {
    page = Math.min(Math.max(nextPage, 1), totalPages());
  }

  function topBreakdown() {
    const players = filteredCustomRankings().slice(0, reportSize);
    const counts = { forwards: 0, defensemen: 0, goalies: 0 };
    for (const player of players) {
      if (player.position === 'G') counts.goalies += 1;
      else if (player.position === 'D') counts.defensemen += 1;
      else counts.forwards += 1;
    }
    return { total: players.length, ...counts };
  }

  function percent(count, total) {
    return total ? Math.round((count / total) * 100) : 0;
  }

  function startResize(sidebar, event) {
    event.preventDefault();
    const bounds = workspaceElement.getBoundingClientRect();
    const onMove = (moveEvent) => {
      if (sidebar === 'reports') {
        reportsWidth = Math.min(360, Math.max(180, moveEvent.clientX - bounds.left));
      } else {
        editorWidth = Math.min(420, Math.max(240, bounds.right - moveEvent.clientX));
      }
    };
    const onUp = () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  }

  const skaterStatCategories = [
    { key: 'goal', label: 'Goal' },
    { key: 'assist', label: 'Assist' },
    { key: 'shot', label: 'Shot' },
    { key: 'hit', label: 'Hit' },
    { key: 'blocked_shot', label: 'Blocked shot' },
    { key: 'penalty_minute', label: 'Penalty minute' },
    { key: 'plus_minus', label: 'Plus/minus' },
    { key: 'power_play_goal', label: 'Power-play goal' },
    { key: 'power_play_assist', label: 'Power-play assist' },
    { key: 'shorthanded_goal', label: 'Shorthanded goal' },
    { key: 'shorthanded_assist', label: 'Shorthanded assist' }
  ];
  const goalieStatCategories = [
    { key: 'win', label: 'Win' },
    { key: 'save', label: 'Save' },
    { key: 'goal_against', label: 'Goal against' },
    { key: 'shutout', label: 'Shutout' }
  ];

  function activeStatCategories() {
    if (playerType === 'goalie') return goalieStatCategories;
    if (playerType === 'skater') return skaterStatCategories;
    return [...skaterStatCategories, ...goalieStatCategories];
  }

  function visibleProfiles() {
    return profiles;
  }

  function defaultProfile() {
    return visibleProfiles().find((profile) => profile.name === 'Yahoo Default Points League') ?? visibleProfiles()[0];
  }
</script>

<svelte:head>
  <title>Fantasy Hockey Stats</title>
  <meta name="description" content="Compare fantasy hockey scoring systems." />
</svelte:head>

<main>
  <section class="controls" aria-label="Ranking filters">
    <label>
      Players
      <select value={playerType} on:change={(event) => selectPlayerType(event.currentTarget.value)} disabled={loading}>
        <option value="all">All players</option>
        <option value="skater">Skaters</option>
        <option value="goalie">Goalies</option>
      </select>
    </label>
    <label>
      Position
      <select value={positionFilter} on:change={(event) => selectPosition(event.currentTarget.value)} disabled={loading}>
        <option value="all">All positions</option>
        {#each availablePositions() as position}
          <option value={position}>{positionLabel(position)}</option>
        {/each}
      </select>
    </label>
    <label>
      Season
      <select bind:value={selectedSeason} on:change={updateRankings} disabled={loading}>
        {#each seasons as season}
          <option value={season.season_id}>{seasonLabel(season.season_id)}</option>
        {/each}
      </select>
    </label>

  </section>

  <div bind:this={workspaceElement} class="workspace" style={`--reports-width: ${reportsWidth}px; --editor-width: ${editorWidth}px;`} class:with-reports={playerType === 'all'} class:reports-collapsed={reportsCollapsed} class:editor-collapsed={editorCollapsed}>
  {#if playerType === 'all'}
    <aside class="reports-panel" class:collapsed={reportsCollapsed}>
      <button class="sidebar-toggle" type="button" on:click={() => reportsCollapsed = !reportsCollapsed} aria-label="Toggle reports sidebar">
        {reportsCollapsed ? '›' : '‹'}
      </button>
      {#if !reportsCollapsed}
        {@const breakdown = topBreakdown()}
        <div class="reports-content">
          <div class="breakdown-heading">
            <div>
              <p class="eyebrow">Top player breakdown</p>
              <h3>Position mix</h3>
            </div>
            <label class="report-size">
              Top
              <select bind:value={reportSize}>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </label>
          </div>
          <div class="breakdown-cards">
            <article><span>Forwards</span><strong>{breakdown.forwards}</strong><small>{percent(breakdown.forwards, breakdown.total)}%</small></article>
            <article><span>Defensemen</span><strong>{breakdown.defensemen}</strong><small>{percent(breakdown.defensemen, breakdown.total)}%</small></article>
            <article><span>Goalies</span><strong>{breakdown.goalies}</strong><small>{percent(breakdown.goalies, breakdown.total)}%</small></article>
          </div>
        </div>
      {/if}
    </aside>
    {#if !reportsCollapsed}
      <button class="resize-handle reports-resize" type="button" on:pointerdown={(event) => startResize('reports', event)} aria-label="Resize reports sidebar"></button>
    {/if}
  {/if}
  <aside class="editor" class:collapsed={editorCollapsed}>
    <button class="sidebar-toggle" type="button" on:click={() => editorCollapsed = !editorCollapsed} aria-label="Toggle scoring sidebar">
      {editorCollapsed ? '‹' : '›'}
    </button>
    {#if !editorCollapsed}
    <div>
      <p class="eyebrow">Scoring editor</p>
      <h2>Adjust the point values.</h2>
      <p>Changes are a private browser preview; shared profiles remain read-only.</p>
    </div>
    <div class="profile-label">
      <span>Baseline profile</span>
      <span class="profile-name">{currentProfileName()}</span>
    </div>
    <div class="profile-actions">
      <button type="button" on:click={() => showProfiles = !showProfiles}>Choose profile</button>
      <button type="button" on:click={() => showSaveProfile = !showSaveProfile}>Save as new</button>
    </div>
    {#if showProfiles}
      <div class="saved-profiles">
        {#each profiles as profile}
          <button type="button" class:active={profile.id === Number(selectedProfile)} on:click={() => chooseProfile(profile.id)}>{profile.name}</button>
        {/each}
      </div>
    {/if}
    {#if showSaveProfile}
      <form class="save-profile" on:submit|preventDefault={saveProfile}>
        <label>
          Profile name
          <input bind:value={newProfileName} maxlength="120" placeholder="My scoring profile" />
        </label>
        {#if profileError}<p class="profile-error">{profileError}</p>{/if}
        <button class="primary" type="submit" disabled={savingProfile}>{savingProfile ? 'Saving…' : 'Save profile'}</button>
      </form>
    {/if}
    {#if draftRules.length}
      <form on:submit|preventDefault={updateRankings}>
        <div class="rule-grid">
          {#if playerType !== 'goalie'}
            <section class="rule-section">
              <h3>Skater stats</h3>
              {#each skaterStatCategories as category, index}
                <label class="rule">
                  <span>{category.label}</span>
                  <input type="number" step="0.1" value={pointsFor(category.key)} on:input={(event) => updatePoints(category.key, event.currentTarget.value)} aria-label={`${category.label} points`} />
                </label>
              {/each}
            </section>
          {/if}
          {#if playerType !== 'skater'}
            <section class="rule-section">
              <h3>Goalie stats</h3>
              {#each goalieStatCategories as category, index}
                <label class="rule">
                  <span>{category.label}</span>
                  <input type="number" step="0.1" value={pointsFor(category.key)} on:input={(event) => updatePoints(category.key, event.currentTarget.value)} aria-label={`${category.label} points`} />
                </label>
              {/each}
            </section>
          {/if}
        </div>
        <div class="editor-actions">
          <button type="button" on:click={resetProfile}>Reset to profile</button>
          <button class="primary" type="submit" disabled={loading}>Apply scoring</button>
        </div>
      </form>
    {/if}
    {/if}
  </aside>
  {#if !editorCollapsed}
    <button class="resize-handle editor-resize" type="button" on:pointerdown={(event) => startResize('editor', event)} aria-label="Resize scoring sidebar"></button>
  {/if}

  <div class="results">
  {#if error}
    <p class="message error">{error}</p>
  {:else if loading}
    <p class="message">Loading rankings…</p>
  {:else if filteredComparisonRows().length === 0}
    <section class="empty">
      <h2>No {positionFilter === 'all' ? 'imported' : positionLabel(positionFilter)} {playerType === 'goalie' ? 'goalies' : playerType === 'skater' ? 'skaters' : 'players'} for this season.</h2>
      <p>{positionFilter === 'all' ? 'Run the season import to load NHL season totals for this view.' : 'Choose another position or season to view players.'}</p>
    </section>
  {:else}
    <section class="rankings">
      <div class="movers">
        <article>
          <p class="eyebrow">Biggest risers</p>
          {#if movers('up').length}
            <ol>
              {#each movers('up') as player}
                <li><span>{player.player_name}</span><strong>+{player.rank_change}</strong></li>
              {/each}
            </ol>
          {:else}<p class="muted">No rank movement yet.</p>{/if}
        </article>
        <article>
          <p class="eyebrow">Biggest fallers</p>
          {#if movers('down').length}
            <ol>
              {#each movers('down') as player}
                <li><span>{player.player_name}</span><strong>{player.rank_change}</strong></li>
              {/each}
            </ol>
          {:else}<p class="muted">No rank movement yet.</p>{/if}
        </article>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Player</th><th>Pos</th><th>Team</th><th>GP</th>
              {#if playerType === 'goalie'}<th>W</th><th>SV</th><th>GA</th><th>SO</th>{/if}
              {#if playerType === 'skater'}<th>G</th><th>A</th><th>SOG</th><th>HIT</th><th>BLK</th><th>PIM</th><th>+/-</th><th>PPG</th><th>PPA</th><th>SHG</th><th>SHA</th>{/if}
              <th>Rank</th><th>Change</th><th>Custom pts</th>
            </tr>
          </thead>
          <tbody>
            {#each pageRows() as player}
              <tr>
                <td>{player.player_name}</td>
                <td>{player.position}</td>
                <td>{player.teams.join(' / ')}</td>
                <td>{player.games_played}</td>
                {#if playerType === 'goalie'}
                  <td>{player.wins ?? '—'}</td><td>{player.saves ?? '—'}</td><td>{player.goals_against ?? '—'}</td><td>{player.shutouts ?? '—'}</td>
                {/if}
                {#if playerType === 'skater'}
                  <td>{player.goals}</td><td>{player.assists}</td><td>{player.shots}</td><td>{player.hits}</td><td>{player.blocked_shots}</td><td>{player.penalty_minutes}</td><td>{player.plus_minus}</td><td>{player.power_play_goals}</td><td>{player.power_play_assists}</td><td>{player.shorthanded_goals}</td><td>{player.shorthanded_assists}</td>
                {/if}
                <td class="rank">{player.rank}</td>
                <td class:positive={player.rank_change > 0} class:negative={player.rank_change < 0}>
                  {player.rank_change > 0 ? '+' : ''}{player.rank_change}
                </td>
                <td class="points">{player.fantasy_points.toFixed(1)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <nav class="pagination" aria-label="Player table pagination">
        <div class="pagination-pages">
          <button type="button" on:click={() => changePage(page - 1)} disabled={page === 1}>Previous</button>
          <span>Page {page} of {totalPages()}</span>
          <button type="button" on:click={() => changePage(page + 1)} disabled={page === totalPages()}>Next</button>
        </div>
        <div class="pagination-summary">
          <label class="page-size">
            Show
            <select bind:value={pageSize} on:change={setPageSize}>
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
          <span>{(page - 1) * pageSize + 1}–{Math.min(page * pageSize, filteredComparisonRows().length)} of {filteredComparisonRows().length}</span>
        </div>
      </nav>
    </section>
  {/if}
  </div>
  </div>
</main>

<style>
  :global(*) { box-sizing: border-box; }
  :global(body) { margin: 0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #e8f0fb; background: #07111e; }
  main { display: flex; flex-direction: column; width: 100%; height: 100vh; padding: 2.5rem clamp(1.25rem, 4vw, 5rem); overflow: hidden; }
  .eyebrow { margin: 0; color: #63d6ff; font-size: .75rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
  h2 { margin: .35rem 0; letter-spacing: -.03em; }
  .controls { display: flex; flex: none; gap: 1rem; margin: 0 0 1.25rem; }
  label { display: grid; gap: .45rem; color: #a9bed3; font-size: .85rem; font-weight: 650; }
  .profile-label { display: grid; gap: .45rem; color: #a9bed3; font-size: .85rem; font-weight: 650; }
  select { min-width: 180px; padding: .7rem .8rem; border: 1px solid #28425d; border-radius: .45rem; color: #f2f8ff; background: #102033; font: inherit; }
  .profile-name { min-width: 180px; padding: .7rem .8rem; border: 1px solid #28425d; border-radius: .45rem; color: #f2f8ff; background: #102033; }
  .profile-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem; }
  .profile-actions button { padding: .5rem; font-size: .8rem; }
  .saved-profiles { display: grid; gap: .45rem; }
  .saved-profiles button { text-align: left; }
  .saved-profiles button.active { border-color: #6dd4fb; color: #eafbff; }
  .save-profile { display: grid; gap: .7rem; padding: .8rem; border: 1px solid #243b54; border-radius: .5rem; }
  .save-profile input { width: 100%; text-align: left; }
  .profile-error { margin: 0; color: #ffb4ad; font-size: .8rem; }
  .workspace { position: relative; display: grid; flex: 1; min-height: 0; grid-template-columns: minmax(0, 1fr) var(--editor-width); gap: 1.5rem; overflow: hidden; }
  .workspace.with-reports { grid-template-columns: var(--reports-width) minmax(0, 1fr) var(--editor-width); }
  .workspace.with-reports.reports-collapsed { grid-template-columns: 48px minmax(0, 1fr) var(--editor-width); }
  .workspace.editor-collapsed { grid-template-columns: minmax(0, 1fr) 48px; }
  .workspace.with-reports.editor-collapsed { grid-template-columns: var(--reports-width) minmax(0, 1fr) 48px; }
  .workspace.with-reports.reports-collapsed.editor-collapsed { grid-template-columns: 48px minmax(0, 1fr) 48px; }
  .results { grid-column: 1; grid-row: 1; min-width: 0; min-height: 0; overflow-y: auto; padding-right: .35rem; }
  .with-reports .results { grid-column: 2; }
  .editor, .reports-panel { min-height: 0; display: grid; align-content: start; gap: 1.25rem; overflow-y: auto; padding: 1.25rem; border: 1px solid #1d354e; border-radius: .8rem; background: #0d1a2a; }
  .editor { grid-column: 2; grid-row: 1; }
  .with-reports .editor { grid-column: 3; }
  .reports-panel { grid-column: 1; grid-row: 1; }
  .editor.collapsed, .reports-panel.collapsed { padding: .4rem; overflow: hidden; }
  .sidebar-toggle { width: 100%; padding: .45rem; color: #83dafa; background: #102033; }
  .resize-handle { position: absolute; z-index: 2; top: 0; bottom: 0; width: 10px; padding: 0; border: 0; border-radius: 0; background: transparent; cursor: col-resize; }
  .resize-handle::after { position: absolute; top: 35%; bottom: 35%; left: 4px; width: 2px; border-radius: 2px; background: #3d5d79; content: ''; }
  .resize-handle:hover::after, .resize-handle:focus-visible::after { background: #83dafa; }
  .reports-resize { left: calc(var(--reports-width) + .7rem); }
  .editor-resize { right: calc(var(--editor-width) + .7rem); }
  .reports-content { display: grid; gap: 1.25rem; }
  .editor h2 { font-size: 1.4rem; }
  .editor p:not(.eyebrow) { color: #9db2ca; line-height: 1.5; }
  .rule-grid { display: grid; gap: .65rem; }
  .rule-section { display: grid; gap: .65rem; }
  .rule-section h3 { margin: .25rem 0 0; color: #d9e8f6; font-size: .9rem; }
  .rule { display: flex; align-items: center; justify-content: space-between; gap: .6rem; padding: .6rem .7rem; border: 1px solid #243b54; border-radius: .45rem; color: #b7c9db; font-size: .85rem; }
  input { width: 4.8rem; padding: .4rem; border: 1px solid #35536f; border-radius: .3rem; color: #f2f8ff; background: #102033; font: inherit; text-align: right; appearance: textfield; }
  input::-webkit-inner-spin-button, input::-webkit-outer-spin-button { margin: 0; appearance: none; }
  .editor-actions { display: flex; justify-content: end; gap: .7rem; margin-top: 1rem; }
  button { padding: .65rem .85rem; border: 1px solid #3d5d79; border-radius: .4rem; color: #cae7fb; background: #122840; font: inherit; cursor: pointer; }
  button.primary { border-color: #6dd4fb; color: #06131f; background: #83dafa; font-weight: 700; }
  button:disabled { cursor: wait; opacity: .6; }
  .rankings, .empty { border: 1px solid #1d354e; border-radius: .8rem; background: #0d1a2a; overflow: hidden; }
  .page-size { display: flex; align-items: center; gap: .4rem; color: #8da4bc; font-weight: 500; }
  .page-size select { min-width: auto; padding: .35rem .45rem; }
  .table-wrap { overflow-x: auto; border-top: 1px solid #1d354e; }
  .movers { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border-top: 1px solid #1d354e; }
  .movers article { min-height: 154px; padding: 1.25rem 1.5rem; }
  .movers article + article { border-left: 1px solid #1d354e; }
  .movers ol { display: grid; gap: .55rem; margin: .8rem 0 0; padding: 0; list-style: none; }
  .movers li { display: flex; justify-content: space-between; color: #c5d7e8; font-size: .9rem; }
  .movers strong { color: #7ee7b4; }
  .movers article:last-child strong { color: #ffa99f; }
  .breakdown-heading { display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: .75rem; }
  .breakdown-heading h3 { margin: .25rem 0 0; font-size: 1rem; }
  .report-size { display: grid; grid-template-columns: auto 62px; align-items: center; gap: .4rem; }
  .report-size select { width: 62px; min-width: 0; padding: .4rem .3rem; }
  .breakdown-cards { display: grid; gap: .75rem; margin-top: 1rem; }
  .breakdown-cards article { display: grid; gap: .2rem; padding: .8rem; border: 1px solid #28425d; border-radius: .45rem; background: #102033; }
  .breakdown-cards span, .breakdown-cards small { color: #9db2ca; font-size: .8rem; }
  .breakdown-cards strong { color: #f2f8ff; font-size: 1.4rem; }
  .muted { margin: .8rem 0 0; color: #718aa3; font-size: .9rem; }
  table { width: 100%; border-collapse: collapse; text-align: left; }
  th, td { padding: 1rem 1.5rem; border-bottom: 1px solid #182d43; white-space: nowrap; }
  th { color: #86a0ba; font-size: .75rem; letter-spacing: .07em; text-transform: uppercase; }
  tr:last-child td { border-bottom: 0; }
  .rank { color: #75d6fd; font-weight: 750; }
  .points { color: #f4c667; font-weight: 750; }
  .pagination { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 1rem 1.5rem; border-top: 1px solid #1d354e; color: #9db2ca; font-size: .9rem; }
  .pagination-pages { display: flex; grid-column: 2; align-items: center; gap: .8rem; }
  .pagination-summary { display: flex; grid-column: 3; justify-self: end; align-items: center; gap: .8rem; }
  .positive { color: #7ee7b4; font-weight: 750; }
  .negative { color: #ffa99f; font-weight: 750; }
  .message { padding: 2rem 0; color: #9db2ca; }
  .error { color: #ffb4ad; }
  .empty { padding: 2.25rem; color: #aabdd0; }
  .empty p { margin-bottom: 0; }
  @media (max-width: 880px) { main { display: block; height: auto; min-height: 100vh; padding: 2.5rem 1rem; overflow: visible; } .controls { flex-direction: column; } select { width: 100%; } .workspace, .workspace.with-reports, .workspace.with-reports.reports-collapsed, .workspace.editor-collapsed, .workspace.with-reports.editor-collapsed, .workspace.with-reports.reports-collapsed.editor-collapsed { display: grid; grid-template-columns: 1fr; overflow: visible; } .results, .with-reports .results, .editor, .with-reports .editor, .reports-panel { grid-column: 1; min-height: auto; overflow: visible; } .results { grid-row: 1; padding-right: 0; } .reports-panel { grid-row: 2; } .editor { grid-row: 3; } .editor.collapsed, .reports-panel.collapsed { min-height: 3rem; } .resize-handle { display: none; } .movers { grid-template-columns: 1fr; } .movers article + article { border-top: 1px solid #1d354e; border-left: 0; } th, td { padding: .8rem 1rem; } }
  @media (max-width: 440px) { .rule-grid { grid-template-columns: 1fr; } .editor-actions { justify-content: stretch; } .editor-actions button { flex: 1; } }
</style>
