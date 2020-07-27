import axios from 'axios'

const axiosWrapper = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL,
  withCredentials: true
})

axiosWrapper.interceptors.response.use(
  response => {
    return response
  },
  error => {
    if (error.response.status === 401) {
      window.location.href = '/login'
    } else {
      return Promise.reject(error)
    }
  }
)

export default axiosWrapper
