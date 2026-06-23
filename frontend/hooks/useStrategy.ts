import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { strategyApi } from "@/lib/api";
import type { GTMStrategy } from "@/types";

interface CompanyProfile {
  name: string;
  website?: string;
  industry: string;
  stage: string;
  description: string;
  founded_year?: number;
}

interface GenerateResponse {
  session_id: string;
  strategy_id?: string;
}

export function useStrategy(id: string | undefined) {
  return useQuery<GTMStrategy>({
    queryKey: ["strategy", id],
    queryFn: () => strategyApi.get(id!),
    enabled: !!id,
  });
}

export function useGenerateStrategy() {
  const queryClient = useQueryClient();

  return useMutation<GenerateResponse, Error, CompanyProfile>({
    mutationFn: (profile) =>
      strategyApi.generate({ company_profile: profile, additional_context: null }) as Promise<GenerateResponse>,
    onSuccess: (data) => {
      if (data.strategy_id) {
        queryClient.invalidateQueries({ queryKey: ["strategy", data.strategy_id] });
      }
    },
  });
}
