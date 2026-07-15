import React from "react";

export default function ReportFilters({
  properties = [],
  propertyId,
  setPropertyId,

  status,
  setStatus,

  search,
  setSearch,

  startDate,
  setStartDate,

  endDate,
  setEndDate,

  showDates = false,
}) {
  return (
    <div className="card mb-md">
      <div
        className="grid gap-md"
        style={{
          gridTemplateColumns: showDates
            ? "repeat(auto-fit,minmax(220px,1fr))"
            : "repeat(auto-fit,minmax(250px,1fr))",
        }}
      >
        {/* Property */}
        <div className="form-group">
          <label htmlFor="property">
            Property
          </label>

          <select
            id="property"
            className="input"
            value={propertyId}
            onChange={(e) => setPropertyId(e.target.value)}
          >
            <option value="">All Properties</option>

            {(properties || []).map((property) => (
              <option
                key={property.id}
                value={property.id}
              >
                {property.name}
              </option>
            ))}
          </select>
        </div>

        {/* Status */}
        <div className="form-group">
          <label htmlFor="status">
            Lease Status
          </label>

          <select
            id="status"
            className="input"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="terminated">Terminated</option>
          </select>
        </div>

        {/* Search */}
        <div className="form-group">
          <label htmlFor="search">
            Tenant Search
          </label>

          <input
            id="search"
            type="text"
            className="input"
            placeholder="Search tenant..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Date filters */}
        {showDates && (
          <>
            <div className="form-group">
              <label htmlFor="start">
                From
              </label>

              <input
                id="start"
                type="date"
                className="input"
                value={startDate}
                onChange={(e) =>
                  setStartDate(e.target.value)
                }
              />
            </div>

            <div className="form-group">
              <label htmlFor="end">
                To
              </label>

              <input
                id="end"
                type="date"
                className="input"
                value={endDate}
                onChange={(e) =>
                  setEndDate(e.target.value)
                }
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}