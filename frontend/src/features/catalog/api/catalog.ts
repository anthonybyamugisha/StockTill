import { apiClient } from '../../../shared/http/client';

export interface Product {
  id: string;
  name: string;
  description: string;
  sku: string;
  barcode: string | null;
  category_id: string | null;
  buying_cost: string;
  selling_price: string;
  minimum_stock_level: number;
  image_url: string | null;
  is_active: boolean;
}

export interface Category {
  id: string;
  name: string;
  description: string;
  parent_id: string | null;
  is_active: boolean;
}

export async function listCategories(activeOnly = true): Promise<Category[]> {
  const res = await apiClient.get<Category[]>('/catalog/categories/', {
    params: { active_only: activeOnly },
  });
  return res.data;
}

export async function createCategory(data: {
  name: string;
  description?: string;
  parent_id?: string | null;
}): Promise<Category> {
  const res = await apiClient.post<Category>('/catalog/categories/', data);
  return res.data;
}

export async function updateCategory(id: string, data: Partial<Category>): Promise<Category> {
  const res = await apiClient.patch<Category>(`/catalog/categories/${id}/`, data);
  return res.data;
}

export async function deactivateCategory(id: string): Promise<void> {
  await apiClient.delete(`/catalog/categories/${id}/`);
}

export async function listProducts(options: { activeOnly?: boolean } = {}): Promise<Product[]> {
  const res = await apiClient.get<Product[]>('/catalog/products/', {
    params: { active_only: options.activeOnly ?? true },
  });
  return res.data;
}

export async function createProduct(data: Partial<Product>): Promise<Product> {
  const res = await apiClient.post<Product>('/catalog/products/', data);
  return res.data;
}

export async function updateProduct(id: string, data: Partial<Product>): Promise<Product> {
  const res = await apiClient.patch<Product>(`/catalog/products/${id}/`, data);
  return res.data;
}

export async function deactivateProduct(id: string): Promise<void> {
  await apiClient.delete(`/catalog/products/${id}/`);
}
