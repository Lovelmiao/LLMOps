export const isLogin = () => {
  return localStorage.getItem('is_login') === 'true'
}

export const setLogin = () => {
  localStorage.setItem('is_login', 'true')
}

export const clearLogin = () => {
  localStorage.removeItem('is_login')
}
