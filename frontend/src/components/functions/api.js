import api from 'services/api'

const fetchGameData = async (gameId, apiEndpoint) => {
  // helper function for components whose data can be retrieved just passing a gameId
  return await apiPost(apiEndpoint, {
    game_id: gameId,
    withCredentials: true
  })
}

// helper function to fetch api providing an endpoint and json post data
const apiPost = async (endpoint, data) => {
  const response = await api.post(`/api/${endpoint}`, data)
  return response.data
}

export { apiPost, fetchGameData }
