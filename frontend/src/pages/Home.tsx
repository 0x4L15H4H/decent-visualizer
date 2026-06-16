function Home() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Shots</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Your espresso shot history.
        </p>
      </div>

      <div className="rounded-lg border border-border-default bg-bg-surface p-4">
        <p className="text-sm text-text-secondary">
          No shots yet. Upload a shot from the Decent Espresso app to get
          started.
        </p>
      </div>
    </div>
  );
}

export default Home;
