import { useEffect, useState } from "react";
import { api } from "../api";

function Home() {
  const [health, setHealth] = useState<string>("loading...");
  const [ping, setPing] = useState<string>("loading...");

  useEffect(() => {
    api
      .get("/api/health")
      .then((res) => res.json())
      .then((data) => setHealth(data.status))
      .catch(() => setHealth("error"));

    api
      .get("/api/ping")
      .then((res) => res.json())
      .then((data) => setPing(`${data.message} @ ${data.timestamp}`))
      .catch(() => setPing("error"));
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold">Home</h1>
      <p className="mt-2 text-gray-600">Welcome to Decent Visualizer.</p>
      <div className="mt-4 rounded-lg bg-white p-4 shadow">
        <p className="text-sm text-gray-500">Backend status:</p>
        <p className="mt-1 text-lg font-semibold">{health}</p>
      </div>
      <div className="mt-4 rounded-lg bg-white p-4 shadow">
        <p className="text-sm text-gray-500">Ping response:</p>
        <p className="mt-1 text-lg font-semibold">{ping}</p>
      </div>
    </div>
  );
}

export default Home;
