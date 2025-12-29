'use server';

/**
 * @fileOverview Generates interview questions tailored to a candidate's resume.
 *
 * - generateCandidateQuestions - A function that generates interview questions.
 * - GenerateCandidateQuestionsInput - The input type for the generateCandidateQuestions function.
 * - GenerateCandidateQuestionsOutput - The return type for the generateCandidateQuestions function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const GenerateCandidateQuestionsInputSchema = z.object({
  resumeText: z.string().describe('The text content of the candidate\'s resume.'),
  jobDescription: z.string().optional().describe('The job description for the role, if available.'),
  numQuestions: z.number().default(5).describe('The number of interview questions to generate.'),
});
export type GenerateCandidateQuestionsInput = z.infer<
  typeof GenerateCandidateQuestionsInputSchema
>;

const GenerateCandidateQuestionsOutputSchema = z.object({
  questions: z.array(z.string()).describe('An array of generated interview questions.'),
});
export type GenerateCandidateQuestionsOutput = z.infer<
  typeof GenerateCandidateQuestionsOutputSchema
>;

export async function generateCandidateQuestions(
  input: GenerateCandidateQuestionsInput
): Promise<GenerateCandidateQuestionsOutput> {
  return generateCandidateQuestionsFlow(input);
}

const prompt = ai.definePrompt({
  name: 'generateCandidateQuestionsPrompt',
  input: {schema: GenerateCandidateQuestionsInputSchema},
  output: {schema: GenerateCandidateQuestionsOutputSchema},
  prompt: `You are an expert HR professional specializing in creating interview questions.

  Based on the provided resume and job description, generate {{numQuestions}} relevant interview questions to assess the candidate's suitability for the role.

  Resume:
  {{resumeText}}

  Job Description (if available):
  {{#if jobDescription}}
  {{jobDescription}}
  {{else}}
  No job description provided.
  {{/if}}

  Ensure the questions are open-ended and designed to evaluate the candidate's skills, experience, and cultural fit.
  Format the output as a JSON array of strings. Do not include any other text besides the JSON.
  `, // Ensure valid json.
});

const generateCandidateQuestionsFlow = ai.defineFlow(
  {
    name: 'generateCandidateQuestionsFlow',
    inputSchema: GenerateCandidateQuestionsInputSchema,
    outputSchema: GenerateCandidateQuestionsOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
