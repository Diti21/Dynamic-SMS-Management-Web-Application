import React, { useEffect, useState } from "react";
import axios from "axios";
import { Line, Bar } from "react-chartjs-2";
import "chart.js/auto";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const Dashboard = () => {
  const [countryOperatorPairs, setCountryOperatorPairs] = useState([]);
  const [prioritizedPairs, setPrioritizedPairs] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [chartData, setChartData] = useState({});
  const [newPair, setNewPair] = useState({ country: "", operator: "", priority: false });
  const [loading, setLoading] = useState(true);

  // Fetch configurations from MongoDB
  const fetchConfigurations = async () => {
    try {
      const response = await axios.get("http://localhost:8000/get-configurations");
      setCountryOperatorPairs(response.data);
      setPrioritizedPairs(response.data.filter((pair) => pair.priority));
    } catch (error) {
      console.error("Error fetching configurations:", error);
    }
  };

  // Fetch SMS metrics from MySQL
  const fetchSMSMetrics = async () => {
    try {
      const response = await axios.get("http://localhost:8000/get-sms-metrics");
      setMetrics(response.data);
      setLoading(false);
      updateChartData(response.data);
    } catch (error) {
      console.error("Error fetching SMS metrics:", error);
    }
  };

  // Update chart data based on SMS metrics
  const updateChartData = (metricsData) => {
    const countryOperators = metricsData.map((metric) => metric.country_operator);
    const smsSent = metricsData.map((metric) => metric.sms_sent);
    const successRates = metricsData.map((metric) => metric.success_rate);
    const failures = metricsData.map((metric) => metric.failures);

    setChartData({
      labels: countryOperators,
      datasets: [
        {
          label: "SMS Sent",
          data: smsSent,
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          borderColor: "rgba(75, 192, 192, 1)",
          borderWidth: 1,
        },
        {
          label: "Success Rates",
          data: successRates,
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1,
        },
        {
          label: "Failures",
          data: failures,
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          borderColor: "rgba(255, 99, 132, 1)",
          borderWidth: 1,
        },
      ],
    });
  };

  // Add a new configuration to MongoDB
  const addConfiguration = async () => {
    try {
      await axios.post("http://localhost:8000/add-configuration", newPair);
      fetchConfigurations();
      setNewPair({ country: "", operator: "", priority: false });
    } catch (error) {
      console.error("Error adding configuration:", error);
    }
  };

  // Control program state (start/stop/restart) for a specific country-operator
  const controlProgram = async (countryOperator, action) => {
    try {
      await axios.post("http://localhost:8000/control-program", {
        country_operator: countryOperator,
        action: action,
      });
      alert(`${action} action sent for ${countryOperator}`);
    } catch (error) {
      console.error("Error controlling program:", error);
    }
  };

  // Fetch configurations and metrics on component mount
  useEffect(() => {
    fetchConfigurations();
    fetchSMSMetrics();
    const intervalId = setInterval(fetchSMSMetrics, 60000); // Refresh metrics every minute
    return () => clearInterval(intervalId);
  }, []);

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <h2>Real-Time SMS Metrics</h2>
      <div style={{ width: "70%", margin: "0 auto" }}>
        {/* Line Chart for SMS Metrics */}
        <Line
          data={chartData}
          options={{
            responsive: true,
            plugins: {
              legend: { position: "top" },
              title: { display: true, text: "SMS Metrics by Country-Operator" },
            },
          }}
        />

        {/* Bar Chart for Success and Failures */}
        <Bar
          data={chartData}
          options={{
            responsive: true,
            plugins: {
              legend: { position: "top" },
              title: { display: true, text: "Failures and Success Rates by Country-Operator" },
            },
          }}
        />
      </div>

      {/* Program Controls */}
      <h3>Program Controls</h3>
      {countryOperatorPairs.map((pair) => (
        <div key={pair.country + pair.operator}>
          <span>
            {pair.country} - {pair.operator}{" "}
            {pair.priority && <strong>(High Priority)</strong>}
          </span>
          <button onClick={() => controlProgram(pair.country_operator, "start")}>Start</button>
          <button onClick={() => controlProgram(pair.country_operator, "stop")}>Stop</button>
          <button onClick={() => controlProgram(pair.country_operator, "restart")}>Restart</button>
        </div>
      ))}

      {/* Form to Add New Country-Operator Pair */}
      <h3>Add Country-Operator Pair</h3>
      <input
        type="text"
        placeholder="Country"
        value={newPair.country}
        onChange={(e) => setNewPair({ ...newPair, country: e.target.value })}
      />
      <input
        type="text"
        placeholder="Operator"
        value={newPair.operator}
        onChange={(e) => setNewPair({ ...newPair, operator: e.target.value })}
      />
      <label>
        <input
          type="checkbox"
          checked={newPair.priority}
          onChange={(e) => setNewPair({ ...newPair, priority: e.target.checked })}
        />
        High Priority
      </label>
      <button onClick={addConfiguration}>Add Pair</button>

      {/* Display High-Priority Pairs */}
      <h3>High Priority Country-Operator Pairs</h3>
      {prioritizedPairs.length > 0 ? (
        prioritizedPairs.map((pair) => (
          <div key={pair.country + pair.operator}>
            {pair.country} - {pair.operator}
          </div>
        ))
      ) : (
        <p>No high-priority pairs.</p>
      )}
    </div>
  );
};

export default Dashboard;
