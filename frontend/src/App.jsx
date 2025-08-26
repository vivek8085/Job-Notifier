import { useEffect, useState } from "react";

function App() {
  const [sites, setSites] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");

  // Fetch sites
  const fetchSites = () => {
    fetch("http://127.0.0.1:8000/sites")
      .then(res => res.json())
      .then(data => setSites(data.sites || []));
  };

  // Fetch jobs
  const fetchJobs = () => {
    fetch("http://127.0.0.1:8000/jobs")
      .then(res => res.json())
      .then(data => setJobs(data.jobs || []));
  };

  useEffect(() => {
    fetchSites();
    fetchJobs();
  }, []);

  // Add site
  const addSite = async () => {
    if (!name || !url) return alert("Enter both name and URL");

    const res = await fetch("http://127.0.0.1:8000/sites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, url }),
    });

    if (res.ok) {
      fetchSites();
      setName("");
      setUrl("");
    } else {
      alert("Failed to add site");
    }
  };

  // Delete site
  const deleteSite = async (siteName) => {
    await fetch(`http://127.0.0.1:8000/sites/${siteName}`, { method: "DELETE" });
    fetchSites();
  };

  // Manual check now
  const checkNow = async () => {
    const res = await fetch("http://127.0.0.1:8000/check_now");
    const data = await res.json();
    alert("Scraper Run:\n" + data.checked.join("\n"));
    fetchJobs();
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Job Site Monitor</h1>

      {/* Add Site Form */}
      <div className="flex gap-2 mb-6">
        <input
          className="border p-2 flex-1 rounded"
          placeholder="Site Name (e.g., ISRO)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="border p-2 flex-1 rounded"
          placeholder="Site URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button
          className="bg-blue-500 text-white px-4 rounded"
          onClick={addSite}
        >
          Add
        </button>
      </div>

      {/* Site List */}
      <h2 className="text-xl font-semibold mb-2">Monitored Sites</h2>
      <ul className="space-y-2 mb-6">
        {sites.map((site, idx) => (
          <li
            key={idx}
            className="flex justify-between items-center border p-2 rounded"
          >
            <span>
              {site.name} —{" "}
              <a href={site.url} className="text-blue-600" target="_blank">
                {site.url}
              </a>
            </span>
            <button
              className="bg-red-500 text-white px-3 rounded"
              onClick={() => deleteSite(site.name)}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>

      {/* Manual Check Button */}
      <button
        className="bg-green-500 text-white px-4 py-2 rounded mb-4"
        onClick={checkNow}
      >
        Check Now
      </button>

      {/* Job List */}
      <h2 className="text-xl font-semibold mb-2">Latest Jobs</h2>
      <ul className="space-y-2">
        {jobs.map((job, idx) => (
          <li key={idx} className="border p-2 rounded">
            <a href={job.link} target="_blank" className="text-blue-600 font-medium">
              {job.title}
            </a>
            <p className="text-sm text-gray-500">{job.site}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
