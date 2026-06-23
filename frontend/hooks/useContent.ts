import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { contentApi } from "@/lib/api";
import type { ContentAsset } from "@/types";

interface GenerateContentInput {
  strategy_id?: string;
  content_types: string[];
  count_per_type: number;
}

interface GenerateContentResponse {
  content_assets: ContentAsset[];
  session_id?: string;
}

export function useContentList() {
  return useQuery<ContentAsset[]>({
    queryKey: ["content"],
    queryFn: () => contentApi.list(),
  });
}

export function useGenerateContent() {
  const queryClient = useQueryClient();

  return useMutation<GenerateContentResponse, Error, GenerateContentInput>({
    mutationFn: (input) =>
      contentApi.generate(input) as Promise<GenerateContentResponse>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content"] });
    },
  });
}
