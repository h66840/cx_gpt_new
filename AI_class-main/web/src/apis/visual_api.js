import { apiRequest, apiPost } from './base'
import { useUserStore } from '@/stores/user'

export const getSceneGraph = async (formData) => {
  return await apiRequest(
    '/api/visual/generate_scene_graph',
    {
      method: 'POST',
      body: formData
      // headers: {} // Content-Type is handled by apiRequest for FormData
    },
    false
  )
}

export function getSuggestionFromSceneGraph(sceneGraph) {
  return apiPost('/api/visual/suggestion', { scene_graph: sceneGraph })
}

export const analyzeShortcomingsStream = async (imageFile, sceneGraphJson) => {
  const formData = new FormData()
  formData.append('image', imageFile)
  formData.append('scene_graph_json', JSON.stringify(sceneGraphJson))

  const userStore = useUserStore()
  const requestOptions = {
    method: 'POST',
    body: formData,
    headers: {}
  }

  if (userStore.isLoggedIn) {
    Object.assign(requestOptions.headers, userStore.getAuthHeaders())
  }

  const response = await fetch('/api/visual/analyze_shortcomings', requestOptions)

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || '流式分析请求失败')
  }

  return response.body.getReader()
}
