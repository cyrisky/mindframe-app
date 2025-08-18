import {
  Interpretation,
  PersonalValuesResults,
  PersonalityResults,
  PersonalValuesDimension,
  PersonalityDimensionLevel
} from '../interpretation';

describe('Interpretation Types', () => {
  describe('Personal Values Types', () => {
    it('should allow valid personal values dimension', () => {
      const dimension: PersonalValuesDimension = {
        title: 'Prestasi (Achievement)',
        description: 'Bagi Kamu, motivasi utama adalah kesuksesan dan pengakuan.',
        manifestation: 'Kamu adalah orang yang berorientasi pada tujuan.',
        strengthChallenges: 'Kekuatan Kamu adalah ambisi, etos kerja yang kuat.'
      };

      expect(dimension.title).toBe('Prestasi (Achievement)');
      expect(dimension.description).toContain('kesuksesan');
    });

    it('should allow valid personal values results', () => {
      const results: PersonalValuesResults = {
        dimensions: {
          achievement: {
            title: 'Prestasi (Achievement)',
            description: 'Bagi Kamu, motivasi utama adalah kesuksesan dan pengakuan.',
            manifestation: 'Kamu adalah orang yang berorientasi pada tujuan.',
            strengthChallenges: 'Kekuatan Kamu adalah ambisi, etos kerja yang kuat.'
          }
        },
        topN: 3
      };

      expect(results.topN).toBe(3);
      expect(results.dimensions.achievement?.title).toBe('Prestasi (Achievement)');
    });
  });

  describe('Personality Types', () => {
    it('should allow valid personality dimension level', () => {
      const level: PersonalityDimensionLevel = {
        interpretation: 'Kamu memiliki Agreeableness yang cenderung rendah.',
        overview: '',
        aspekKehidupan: {
          gayaBelajar: ['Lebih suka belajar sendiri, di suasana yang tenang.'],
          hubunganInterpersonal: ['Biasanya kamu punya sedikit hubungan yang benar-benar dekat.'],
          karir: ['Kamu cocok di pekerjaan yang butuh analisis rasional.'],
          kekuatan: ['Kamu mandiri dan objektif.'],
          kelemahan: ['Kamu mungkin terlihat kurang peduli atau empati.'],
          kepemimpinan: ['Tegas dan fokus pada hasil.']
        },
        rekomendasi: [
          {
            title: 'Empati & Perspektif',
            description: 'Latih empati dengan lebih sering mendengarkan secara aktif.'
          }
        ]
      };

      expect(level.interpretation).toContain('Agreeableness');
      expect(level.aspekKehidupan.gayaBelajar).toHaveLength(1);
      expect(level.rekomendasi).toHaveLength(1);
    });

    it('should allow valid personality results', () => {
      const results: PersonalityResults = {
        dimensions: {
          agreeableness: {
            rendah: {
              interpretation: 'Kamu memiliki Agreeableness yang cenderung rendah.',
              overview: '',
              aspekKehidupan: {
                gayaBelajar: ['Lebih suka belajar sendiri.'],
                hubunganInterpersonal: ['Biasanya kamu punya sedikit hubungan yang dekat.'],
                karir: ['Kamu cocok di pekerjaan yang butuh analisis rasional.'],
                kekuatan: ['Kamu mandiri dan objektif.'],
                kelemahan: ['Kamu mungkin terlihat kurang peduli.'],
                kepemimpinan: ['Tegas dan fokus pada hasil.']
              },
              rekomendasi: [
                {
                  title: 'Empati & Perspektif',
                  description: 'Latih empati dengan lebih sering mendengarkan secara aktif.'
                }
              ]
            }
          }
        },
        overview: ''
      };

      expect(results.dimensions.agreeableness?.rendah?.interpretation).toContain('Agreeableness');
    });
  });

  describe('Main Interpretation Type', () => {
    it('should allow valid interpretation with personal values', () => {
      const interpretation: Interpretation = {
        _id: '689d9d259751994f1ef61abb',
        testName: 'personalValues',
        testType: 'top-n-dimension',
        isActive: true,
        results: {
          dimensions: {
            achievement: {
              title: 'Prestasi (Achievement)',
              description: 'Bagi Kamu, motivasi utama adalah kesuksesan dan pengakuan.',
              manifestation: 'Kamu adalah orang yang berorientasi pada tujuan.',
              strengthChallenges: 'Kekuatan Kamu adalah ambisi, etos kerja yang kuat.'
            }
          },
          topN: 3
        },
        createdAt: 'Thu, 10 Aug 2023 10:00:00 GMT',
        updatedAt: 'Thu, 10 Aug 2023 10:00:00 GMT'
      };

      expect(interpretation.testName).toBe('personalValues');
      expect(interpretation.testType).toBe('top-n-dimension');
      expect(interpretation.isActive).toBe(true);
      expect(interpretation.results.topN).toBe(3);
    });

    it('should allow valid interpretation with personality', () => {
      const interpretation: Interpretation = {
        _id: '689d9d4e9751994f1ef61abc',
        testName: 'kepribadian',
        testType: 'multiple-dimension',
        isActive: true,
        results: {
          dimensions: {
            agreeableness: {
              rendah: {
                interpretation: 'Kamu memiliki Agreeableness yang cenderung rendah.',
                overview: '',
                aspekKehidupan: {
                  gayaBelajar: ['Lebih suka belajar sendiri.'],
                  hubunganInterpersonal: ['Biasanya kamu punya sedikit hubungan yang dekat.'],
                  karir: ['Kamu cocok di pekerjaan yang butuh analisis rasional.'],
                  kekuatan: ['Kamu mandiri dan objektif.'],
                  kelemahan: ['Kamu mungkin terlihat kurang peduli.'],
                  kepemimpinan: ['Tegas dan fokus pada hasil.']
                },
                rekomendasi: [
                  {
                    title: 'Empati & Perspektif',
                    description: 'Latih empati dengan lebih sering mendengarkan secara aktif.'
                  }
                ]
              }
            }
          },
          overview: ''
        },
        createdAt: '2023-08-10T10:00:00.000Z',
        updatedAt: '2024-08-10T10:00:00.000Z'
      };

      expect(interpretation.testName).toBe('kepribadian');
      expect(interpretation.testType).toBe('multiple-dimension');
      expect(interpretation.isActive).toBe(true);
    });
  });
});
