import { useState, useEffect } from "react";
import api from "services/api";

const fetchGameData = async (gameId, apiEndpoint) => {
  // helper function for components whose data can be retrieved just passing a gameId
  return await fetchData(apiEndpoint, {
    game_id: gameId,
    withCredentials: true,
  });
};

//helper function to fetch api providing an endpoint and json post data
const fetchData = async (endpoint, data) => {
  const response = await api.post(`/api/${endpoint}`, data);
  return response.data;
};

const isEmpty = function (data) {
  if (typeof data === "object") {
    if (JSON.stringify(data) === "{}" || JSON.stringify(data) === "[]") {
      return true;
    } else if (!data) {
      return true;
    }
    return false;
  } else if (typeof data === "string") {
    if (!data.trim()) {
      return true;
    }
    return false;
  } else if (typeof data === "undefined") {
    return true;
  } else {
    return false;
  }
};

const usePostRequest = (url, payload) => {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState({});

  const postUrl = async (url, payload) => {
    try {
      setLoading(true);
      const response = await api.post(url, {
        withCredentials: true,
        data: payload,
      });
      setData(response.data);
    } catch (error) {
      setError(error);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    postUrl(url, payload);
  }, [url, payload]);

  return {
    data,
    loading,
    error,
  };
};

export { isEmpty, usePostRequest, fetchData, fetchGameData };
