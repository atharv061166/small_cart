import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, ScatterChart, Scatter, ZAxis
} from 'recharts';
import { fetchAdminDashboardData, fetchAdminInventory, fetchAdminProductDetail, fetchAdminSegmentation } from '../api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#a28bfe', '#fd79a8'];

const SEGMENT_PROFILES = {
  champion: { emoji: '🏆', color: '#00C49F', label: 'Champion', desc: 'Recent, frequent buyers with large basket sizes. Your most valuable customers.' },
  regular: { emoji: '🛒', color: '#0088FE', label: 'Regular', desc: 'Steady, loyal shoppers. Moderate frequency and basket size.' },
  'at-risk': { emoji: '⚠️', color: '#FFBB28', label: 'At-Risk', desc: 'Previously active users who are buying less often. Need re-engagement.' },
  dormant: { emoji: '💤', color: '#FF8042', label: 'Dormant', desc: 'Long-inactive users with very high recency. Win-back candidates.' },
};
const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

export default function AdminDashboardPage() {
  const [dashboardData, setDashboardData] = useState(null);
  const [segmentationData, setSegmentationData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Inventory lookup state
  const [searchQuery, setSearchQuery] = useState('');
  const [inventoryList, setInventoryList] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productDetails, setProductDetails] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchAdminDashboardData();
        setDashboardData(data);

        const segData = await fetchAdminSegmentation();
        setSegmentationData(segData);

        // Initial inventory list
        const invData = await fetchAdminInventory('');
        setInventoryList(invData.inventory);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSearch = async (e) => {
    const q = e.target.value;
    setSearchQuery(q);
    if (q.length > 2 || q.length === 0) {
      try {
        const data = await fetchAdminInventory(q);
        setInventoryList(data.inventory);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleSelectProduct = async (e) => {
    const pName = e.target.value;
    if (!pName) {
      setSelectedProduct(null);
      setProductDetails(null);
      return;
    }

    setSelectedProduct(pName);
    try {
      const details = await fetchAdminProductDetail(pName);
      setProductDetails(details);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div className="loading-spinner" />
        <p>Loading Dashboard...</p>
      </div>
    );
  }

  if (!dashboardData) {
    return <div style={{ padding: '2rem' }}>Failed to load dashboard.</div>;
  }

  // Format DOW data
  const dowData = dashboardData.orders_per_dow.map(d => ({
    name: DAY_NAMES[d.order_dow],
    orders: d.order_count
  }));

  // Format Hour data
  const hourData = dashboardData.orders_per_hour.map(d => ({
    hour: `${d.order_hour_of_day}:00`,
    orders: d.order_count
  }));

  // Format Heatmap data (Dept x DOW)
  // Recharts doesn't have a heatmap, so we build a simple HTML table for it
  const depts = [...new Set(dashboardData.dept_demand_dow.map(d => d.department))].sort();
  const maxDeptDemand = Math.max(...dashboardData.dept_demand_dow.map(d => d.order_count));

  const getHeatmapColor = (val) => {
    const intensity = val / maxDeptDemand;
    return `rgba(0, 136, 254, ${intensity * 0.9 + 0.1})`;
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto', background: 'var(--bg-color)', color: 'var(--text-color)' }}>
      <h1 style={{ marginBottom: '2rem', fontSize: '2.5rem', fontWeight: 'bold' }}>Demand & Inventory Dashboard</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '2rem', marginBottom: '2rem' }}>

        {/* Total Orders per Day of Week */}
        <div style={cardStyle}>
          <h2>Total Orders per Day of Week</h2>
          <div style={{ height: '300px', overflow: 'visible', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dowData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="name" tick={{ fill: '#ffffff' }} />
                <YAxis tick={{ fill: '#ffffff' }} />
                <RechartsTooltip wrapperStyle={tooltipWrapperStyle} contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} />
                <Bar dataKey="orders" fill="#0088FE" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Order Volume by Hour */}
        <div style={cardStyle}>
          <h2>Order Volume by Hour of Day</h2>
          <div style={{ height: '300px', overflow: 'visible', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={hourData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="hour" tick={{ fill: '#ffffff' }} />
                <YAxis tick={{ fill: '#ffffff' }} />
                <RechartsTooltip wrapperStyle={tooltipWrapperStyle} contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} />
                <Line type="monotone" dataKey="orders" stroke="#00C49F" strokeWidth={3} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top 10 Products Overall */}
        <div style={cardStyle}>
          <h2>Top 10 Products Overall</h2>
          <div style={{ height: '300px', overflow: 'visible', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dashboardData.top_products_overall} layout="vertical" margin={{ top: 20, right: 30, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis type="number" tick={{ fill: '#ffffff' }} />
                <YAxis dataKey="product_name" type="category" tick={{ fill: '#ffffff', fontSize: 12 }} width={120} />
                <RechartsTooltip wrapperStyle={tooltipWrapperStyle} contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} />
                <Bar dataKey="order_count" fill="#FFBB28" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top 20 Aisles */}
        <div style={cardStyle}>
          <h2>Top 20 Aisles</h2>
          <div style={{ height: '300px', overflow: 'visible', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dashboardData.top_aisles_overall} layout="vertical" margin={{ top: 20, right: 30, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis type="number" tick={{ fill: '#ffffff' }} />
                <YAxis dataKey="aisle" type="category" tick={{ fill: '#ffffff', fontSize: 12 }} width={120} />
                <RechartsTooltip wrapperStyle={tooltipWrapperStyle} contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} />
                <Bar dataKey="order_count" fill="#a28bfe" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Heatmap: Demand by Department vs DOW */}
      <div style={{ ...cardStyle, marginBottom: '2rem' }}>
        <h2>Demand by Department vs Day of Week</h2>
        <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center' }}>
            <thead>
              <tr>
                <th style={thStyle}>Department</th>
                {DAY_NAMES.map(day => <th key={day} style={thStyle}>{day}</th>)}
              </tr>
            </thead>
            <tbody>
              {depts.map(dept => (
                <tr key={dept}>
                  <td style={{ ...tdStyle, fontWeight: 'bold', textAlign: 'left' }}>{dept}</td>
                  {DAY_NAMES.map((day, idx) => {
                    const cellData = dashboardData.dept_demand_dow.find(d => d.department === dept && d.order_dow === idx);
                    const val = cellData ? cellData.order_count : 0;
                    return (
                      <td key={idx} style={{ ...tdStyle, backgroundColor: val > 0 ? getHeatmapColor(val) : 'transparent' }}>
                        <span style={{ color: val > (maxDeptDemand * 0.5) ? '#fff' : 'inherit', fontWeight: val > 0 ? '600' : 'normal' }}>
                          {val}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Product-Level Lookup */}
      <div style={cardStyle}>
        <h2>Product Order Lookup</h2>
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Search product..."
            value={searchQuery}
            onChange={handleSearch}
            style={{ padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: '#ffffff', width: '250px' }}
          />
          <select
            onChange={handleSelectProduct}
            value={selectedProduct || ''}
            style={{ padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: '#ffffffff', flex: 1 }}
          >
            <option value="" style={{ backgroundColor: '#000000', color: '#ffffff' }}>-- Select a Product --</option>
            {inventoryList.map(item => (
              <option key={item.product_name} value={item.product_name} style={{ backgroundColor: '#000000', color: '#ffffff' }}>
                {item.product_name}
              </option>
            ))}
          </select>
        </div>

        {productDetails && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem', alignItems: 'center' }}>

            {/* KPI Cards */}
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <KPICard title="Total Orders" value={productDetails.info.total_orders} />
            </div>

            {/* DOW Demand Chart */}
            <div>
              <h3>Orders by Day of Week</h3>
              <div style={{ height: '250px', marginTop: '1rem', overflow: 'visible', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={DAY_NAMES.map((name, i) => ({ name, orders: productDetails.dow_demand[i.toString()] || 0 }))}
                    margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="name" tick={{ fill: 'var(--text-color)', fontSize: 11 }} />
                    <YAxis tick={{ fill: 'var(--text-color)', fontSize: 11 }} />
                    <RechartsTooltip wrapperStyle={tooltipWrapperStyle} contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} />
                    <Bar dataKey="orders" fill="#8884d8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        )}
      </div>

      {/* Customer Segmentation Section */}
      {segmentationData && (
        <>
          <h2 style={{ marginTop: '3rem', marginBottom: '1.5rem', fontSize: '2rem', fontWeight: 'bold' }}>Customer Segmentation</h2>

          {/* Donut chart — standalone row */}
          <div style={{ marginBottom: '2rem' }}>
            <div style={cardStyle}>
              <h2>User Distribution by Segment</h2>
              <div style={{ height: '300px', overflow: 'visible', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={segmentationData.counts}
                      dataKey="count"
                      nameKey="segment"
                      cx="50%"
                      cy="50%"
                      innerRadius={70}
                      outerRadius={100}
                      label={({ segment, percent }) => `${segment}: ${(percent * 100).toFixed(1)}%`}
                    >
                      {segmentationData.counts.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip wrapperStyle={tooltipWrapperStyle} contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Segment Profile Cards — own card, no gridColumn span needed */}
          <div style={{ ...cardStyle, marginBottom: '2rem' }}>
            <h2>Segment Profiles</h2>
            <p style={{ color: 'var(--text-color)', opacity: 0.6, fontSize: '0.85rem', marginBottom: '1.5rem' }}>
              Behavioural characteristics of each K-Means cluster derived from the feature engineering notebook.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
              {segmentationData.cluster_metrics.map((cm) => {
                const profile = SEGMENT_PROFILES[cm.segment] || {};
                const countEntry = segmentationData.counts.find(c => c.segment === cm.segment);
                return (
                  <div
                    key={cm.segment}
                    style={{
                      background: `linear-gradient(135deg, ${profile.color}18, ${profile.color}08)`,
                      border: `1px solid ${profile.color}44`,
                      borderRadius: '14px',
                      padding: '1.25rem',
                    }}
                  >
                    <div style={{ fontSize: '1.8rem', marginBottom: '0.4rem' }}>{profile.emoji}</div>
                    <div style={{ fontWeight: '700', fontSize: '1.1rem', color: profile.color, marginBottom: '0.4rem', textTransform: 'capitalize' }}>
                      {profile.label || cm.segment}
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-color)', opacity: 0.75, marginBottom: '1rem', lineHeight: 1.5 }}>
                      {profile.desc}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                      <div style={metricPillStyle}>
                        <span style={{ fontSize: '0.72rem', opacity: 0.7, display: 'block' }}>Users</span>
                        <span style={{ fontWeight: '700', color: profile.color }}>{countEntry ? countEntry.count.toLocaleString() : '—'}</span>
                      </div>
                      <div style={metricPillStyle}>
                        <span style={{ fontSize: '0.72rem', opacity: 0.7, display: 'block' }}>Avg Orders</span>
                        <span style={{ fontWeight: '700', color: profile.color }}>{cm.avg_order_number}</span>
                      </div>
                      <div style={{ ...metricPillStyle, gridColumn: '1 / -1' }}>
                        <span style={{ fontSize: '0.72rem', opacity: 0.7, display: 'block' }}>Avg Days Since Last Order</span>
                        <span style={{ fontWeight: '700', color: profile.color }}>{cm.avg_days_since_prior_order} days</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}



    </div>
  );
}

// ── Styles & Components ──

const cardStyle = {
  background: 'var(--card-bg)',
  borderRadius: '16px',
  padding: '1.5rem',
  boxShadow: '0 4px 20px rgba(0,0,0,0.05)',
  border: '1px solid var(--border-color)',
  overflow: 'visible'
};

const tooltipStyle = {
  backgroundColor: 'var(--card-bg)',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  color: 'var(--text-color)',
  zIndex: 1000,
  pointerEvents: 'auto',
  boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
};

const tooltipWrapperStyle = {
  zIndex: 10000
};

const tooltipLabelStyle = {
  color: 'var(--text-color)',
  fontWeight: '600'
};

const tooltipItemStyle = {
  color: 'var(--text-color)'
};

const thStyle = {
  padding: '1rem',
  borderBottom: '2px solid var(--border-color)',
  color: 'var(--text-color)',
  fontWeight: '600',
};

const tdStyle = {
  padding: '0.75rem',
  borderBottom: '1px solid var(--border-color)',
  color: 'var(--text-color)',
};

function KPICard({ title, value }) {
  return (
    <div style={{ background: 'rgba(0,136,254,0.05)', border: '1px solid rgba(0,136,254,0.2)', padding: '1rem', borderRadius: '12px', textAlign: 'center' }}>
      <div style={{ fontSize: '0.9rem', color: 'var(--text-color)', opacity: 0.8, marginBottom: '0.5rem' }}>{title}</div>
      <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#0088FE' }}>{value}</div>
    </div>
  );
}

const metricPillStyle = {
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
  padding: '0.5rem 0.75rem',
  textAlign: 'center',
  color: 'var(--text-color)',
};
