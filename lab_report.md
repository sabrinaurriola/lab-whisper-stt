# Whisper STT Implementation — Evaluation Report

**Project:** Project Nimbus Engineering Meeting  
**Model:** OpenAI Whisper (`whisper-1`)  
**Audio duration:** 5 minutes, 9.2 seconds

## 1. Objective and Implementation

The objective of this lab was to implement a speech-to-text workflow using the OpenAI Whisper API and evaluate how contextual prompting and audio chunking affect transcription results.

I developed the workflow in a Jupyter notebook and converted it into a reusable Python script (`whisper_transcription.py`). The implementation supports guided and unguided transcription, audio chunking, segment-level timestamps, and exports to TXT, SRT, and JSON.

The standalone script executed successfully, generating all five expected output files.

## 2. Guided vs. Unguided Transcription

I transcribed the same meeting recording twice: first without a prompt, then with contextual vocabulary including Project Nimbus, Kubernetes, PostgreSQL, Redis, Amazon EKS, and Q3 OKRs.

The most significant difference was the recognition of the caching technology:

- **Unguided transcription:** "RIDIS cache"
- **Guided transcription:** "Redis cache"

I listened to the corresponding section of the original recording and confirmed that the speaker said "Redis". This demonstrates that contextual prompting improved recognition of this specific technical term.

Other differences, such as "JIRA" versus "Jira" and "Okay" versus "OK", were mainly formatting variations.

However, I did not calculate an overall Word Error Rate (WER), so I cannot conclude that prompting improved the accuracy of the entire transcription.

## 3. Audio Chunking: Benefits and Challenges

I divided the 309.2-second recording into six chunks: five 60-second segments and one final 9.2-second segment.

Chunking makes it possible to process recordings that exceed the API's file-size limit. It also creates smaller units that can be processed and retried individually.

However, fixed-duration chunking introduced a transcription issue near the five-minute boundary. The chunked transcription ended a sentence with "review and draft the log retention plan with", omitting the word "Priya". I verified the missing word by listening to the original recording.

This illustrates how splitting audio in the middle of speech can cause information loss.

## 4. Timestamps and Output Formats

I requested segment-level timestamps using Whisper's `verbose_json` response and converted chunk-relative timestamps into positions within the original recording.

The workflow generated 56 timestamped segments, beginning at 0.0 seconds and ending at 308.0 seconds.

A validation check identified a 1.84-second overlap between estimated segment timestamps at the boundary between Chunks 5 and 6. This demonstrates that independently generated chunk timestamps may require additional validation.

The final outputs included plain-text transcripts, SRT subtitles, and structured JSON suitable for further processing.

## 5. Recommendations and Conclusion

To improve transcription quality, I would:

1. Provide relevant technical vocabulary without suggesting what speakers should say.
2. Split recordings at natural pauses rather than fixed time boundaries, where feasible.
3. Consider overlapping chunks with deduplication to reduce lost words at boundaries.
4. Validate important terminology and timestamps against the original audio.
5. Measure accuracy against a verified reference transcript before claiming overall improvements.

**Conclusion:** The Whisper API successfully supported an end-to-end transcription workflow. Contextual prompting improved recognition of a verified technical term, while chunking introduced identifiable boundary-related quality issues. The main lesson is that successful API execution must be complemented by transcription quality checks before the results are used in business workflows.