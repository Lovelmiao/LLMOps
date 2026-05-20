import { apiPrefix, httpCode } from '@/config'
import { Message } from '@arco-design/web-vue'

const TIME_OUT = 180 * 1000

const baseFetchOptions = {
  method: 'GET',
  mode: 'cors',
  credentials: 'include',
  headers: new Headers({
    'Content-Type': 'application/json',
  }),
  redirect: 'follow',
}

type FetchOptionsType = Omit<RequestInit, 'body'> & {
  params?: Record<string, any>
  body?: BodyInit | Record<string, any> | null
}

const baseFetch = <T>(url: string, fetchOptions: FetchOptionsType): Promise<T> => {
  const options: typeof baseFetchOptions & FetchOptionsType = Object.assign(
    {},
    baseFetchOptions,
    fetchOptions,
  )

  let urlWithPrefix: string = `${apiPrefix}${url.startsWith('/') ? url : `/${url}`}`
  const { method, params, body } = options

  if (method === 'GET' && params) {
    const paramsArray: string[] = []
    Object.keys(params).forEach((key) => {
      paramsArray.push(`${key}=${encodeURIComponent(params[key])}`)
    })

    if (urlWithPrefix.search(/\?/) === -1) {
      urlWithPrefix += `?${paramsArray.join('&')}`
    } else {
      urlWithPrefix += `&${paramsArray.join('&')}`
    }

    delete options.params
  }

  if (body instanceof FormData) {
    options.body = body
    const headers = new Headers(options.headers)
    headers.delete('Content-Type')
    options.headers = headers
  } else if (body) {
    options.body = JSON.stringify(body)
  }

  return Promise.race([
    new Promise((resolve, reject) => {
      setTimeout(() => {
        reject(new Error('接口超时'))
      }, TIME_OUT)
    }),
    new Promise((resolve, reject) => {
      globalThis
        .fetch(urlWithPrefix, options as RequestInit)
        .then(async (res) => {
          const json = await res.json()
          if (json.code === httpCode.success) {
            resolve(json as T)
          } else {
            Message.error(json.message)
            reject(new Error(json.message))
          }
        })
        .catch((err) => {
          Message.error(err.message)
          reject(err)
        })
    }),
  ]) as Promise<T>
}

export const request = <T>(url: string, options = {}) => {
  return baseFetch<T>(url, options)
}

export const get = <T>(url: string, options = {}) => {
  return request<T>(url, Object.assign({}, options, { method: 'GET' }))
}

export const post = <T>(url: string, options = {}) => {
  return request<T>(url, Object.assign({}, options, { method: 'POST' }))
}

export const patch = <T>(url: string, options = {}) => {
  return request<T>(url, Object.assign({}, options, { method: 'PATCH' }))
}

export const del = <T>(url: string, options = {}) => {
  return request<T>(url, Object.assign({}, options, { method: 'DELETE' }))
}
