function ProfileList({ profiles, onSelectProfile, loading }) {
  if (loading) {
    return (
      <div className="border border-black bg-white p-8 text-center">
        <p className="text-lg text-black">Loading profiles...</p>
      </div>
    )
  }

  if (profiles.length === 0) {
    return (
      <div className="border border-black bg-black/5 p-8 text-center">
        <p className="text-lg text-black mb-2">No profiles found</p>
        <p className="text-sm text-black/70">Use Gemini AI tab to fetch company profiles</p>
      </div>
    )
  }

  return (
    <div className="mt-8">
      <h3 className="text-xl font-bold text-black mb-4">
        Company Profiles ({profiles.length})
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {profiles.map((profile) => (
          <div
            key={profile.id}
            className="border border-black bg-white hover:bg-black/5 transition-colors cursor-pointer"
            onClick={() => onSelectProfile(profile)}
          >
            <div className="p-4 border-b border-black flex justify-between items-center">
              <span className="px-3 py-1 bg-black text-white text-sm font-medium">
                {profile.ticker}
              </span>
              <span className="text-xs text-black/70">
                {new Date(profile.created_at).toLocaleDateString()}
              </span>
            </div>
            <div className="p-4">
              <p className="text-sm text-black/70 mb-2">
                {Object.keys(profile.data || {}).length} sections available
              </p>
              {profile.data?.What && (
                <p className="text-base font-medium text-black">
                  {profile.data.What.CompanyName || profile.data.What.Name || 'Company Profile'}
                </p>
              )}
            </div>
            <div className="p-4 border-t border-black">
              <button className="w-full py-2 px-4 bg-black text-white text-sm font-medium hover:bg-black/90 transition-colors">
                View
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ProfileList
