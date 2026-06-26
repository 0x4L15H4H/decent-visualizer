export interface Bean {
  id: string;
  name: string;
  roaster: string;
  producer: string | null;
  farm: string | null;
  country: string | null;
  variety: string | null;
  process: string | null;
  notes: string | null;
  created_at: string;
}

export type BeanFormValues = {
  name: string;
  roaster: string;
  producer: string;
  farm: string;
  country: string;
  variety: string;
  process: string;
  notes: string;
};

export const emptyBeanFormValues: BeanFormValues = {
  name: "",
  roaster: "",
  producer: "",
  farm: "",
  country: "",
  variety: "",
  process: "",
  notes: "",
};

export function valuesFromBean(bean: Bean): BeanFormValues {
  return {
    name: bean.name,
    roaster: bean.roaster,
    producer: bean.producer ?? "",
    farm: bean.farm ?? "",
    country: bean.country ?? "",
    variety: bean.variety ?? "",
    process: bean.process ?? "",
    notes: bean.notes ?? "",
  };
}

export function beanPayload(values: BeanFormValues) {
  return {
    name: values.name,
    roaster: values.roaster,
    producer: values.producer || null,
    farm: values.farm || null,
    country: values.country || null,
    variety: values.variety || null,
    process: values.process || null,
    notes: values.notes || null,
  };
}
