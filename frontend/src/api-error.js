export function throwApiError(response) {
  const error = new Error(`API error: ${response.status}`)
  error.status = response.status
  throw error
}

export function redirectToErrorPage(error) {
  console.error(error)

  const statusCode = [403, 404, 500, 503].includes(error.status) ? error.status : 500
  window.location.replace(`/error/${statusCode}`)
}